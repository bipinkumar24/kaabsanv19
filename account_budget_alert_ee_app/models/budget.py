# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class BudgetLine(models.Model):
    _inherit = "budget.line"

    allow2_manager = fields.Boolean("Allow to Manager")
    warning_type = fields.Selection(
        [('ignore', 'Ignore'), ('warning', 'Warning'), ('restrict', 'Restriction')]
    )
    is_active = fields.Boolean("Active")


class BudgetAlertMixin(models.AbstractModel):
    _name = "budget.alert.mixin"
    _description = "Budget Alert Mixin"

    def _get_budget_domain(self, date_value):
        return [
            ('budget_analytic_id.state', '=', 'confirmed'),
            ('budget_analytic_id.budget_type', '!=', 'revenue'),
            ('date_from', '<=', date_value),
            ('date_to', '>=', date_value),
            ('is_active', '=', True),
        ]

    def _get_matching_budget_lines(self, analytic_accounts, date_value):
        if not analytic_accounts or not date_value:
            return self.env['budget.line']

        domain = self._get_budget_domain(date_value) + [('auto_account_id', 'in', analytic_accounts.ids)]
        return self.env['budget.line'].search(domain)

    def _evaluate_budget_alert(self, budget_lines, amount, label):
        warning_labels = []
        restrict_labels = []
        manager_allowed = False

        for budget_line in budget_lines:
            remaining_amount = abs(budget_line.budget_amount) - abs(budget_line.achieved_amount)
            if amount < remaining_amount:
                continue

            if budget_line.warning_type == 'warning':
                if label not in warning_labels:
                    warning_labels.append(label)
            elif budget_line.warning_type == 'restrict':
                if budget_line.allow2_manager and self.env.user.has_group('account.group_account_manager'):
                    manager_allowed = True
                elif label not in restrict_labels:
                    restrict_labels.append(label)

        return warning_labels, restrict_labels, manager_allowed


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    exceed_note = fields.Char("Warning Info", default="")
    is_warning = fields.Boolean()

    def button_confirm(self):
        for order in self:
            warning_products = []
            restricted_products = []
            manager_allowed = False

            for line in order.order_line:
                budget_lines = self.env['budget.alert.mixin']._get_matching_budget_lines(
                    line.distribution_analytic_account_ids,
                    order.date_order,
                )
                warnings, restrictions, allowed = self.env['budget.alert.mixin']._evaluate_budget_alert(
                    budget_lines,
                    line.price_subtotal,
                    line.product_id.display_name,
                )
                warning_products.extend(x for x in warnings if x not in warning_products)
                restricted_products.extend(x for x in restrictions if x not in restricted_products)
                manager_allowed = manager_allowed or allowed

            if restricted_products:
                raise ValidationError(
                    _("Restriction on Confirm Purchase Order: Budget limit exceeded for products %s")
                    % ', '.join(restricted_products)
                )

            order.is_warning = bool(warning_products or manager_allowed)
            if warning_products:
                order.exceed_note = _("Budget limit exceeded for products: %s.") % ', '.join(warning_products)
            elif manager_allowed:
                order.exceed_note = _("Order amount exceeds the budget amount, but a manager is allowed to confirm it.")
            else:
                order.exceed_note = False

        return super().button_confirm()


class AccountMove(models.Model):
    _inherit = 'account.move'

    exceed_note = fields.Char("Warning Info", default="")
    is_warning = fields.Boolean()

    def action_post(self):
        for move in self:
            warning_accounts = []
            restricted_accounts = []
            manager_allowed = False

            for line in move.invoice_line_ids:
                budget_lines = self.env['budget.alert.mixin']._get_matching_budget_lines(
                    line.distribution_analytic_account_ids,
                    move.invoice_date or move.date,
                )
                warnings, restrictions, allowed = self.env['budget.alert.mixin']._evaluate_budget_alert(
                    budget_lines,
                    line.price_subtotal,
                    line.account_id.display_name,
                )
                warning_accounts.extend(x for x in warnings if x not in warning_accounts)
                restricted_accounts.extend(x for x in restrictions if x not in restricted_accounts)
                manager_allowed = manager_allowed or allowed

            if restricted_accounts:
                raise ValidationError(
                    _("Restriction on Validate Bill: Budget limit exceeded for accounts %s")
                    % ', '.join(restricted_accounts)
                )

            move.is_warning = bool(warning_accounts or manager_allowed)
            if warning_accounts:
                move.exceed_note = _("Budget limit exceeded for accounts: %s.") % ', '.join(warning_accounts)
            elif manager_allowed:
                move.exceed_note = _("Budget limit exceeded, but a manager is allowed to validate the vendor bill.")
            else:
                move.exceed_note = False

        return super().action_post()
