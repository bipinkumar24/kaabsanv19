# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    discount_method = fields.Selection([('fix', 'Fixed'), ('per', 'Percentage')], string='Discount Method')
    discount_amount = fields.Float(string='Discount Amount')
    discount_amt = fields.Monetary(
        string='Discount',
        readonly=True,
        compute='_compute_discount_amounts',
        store=True,
        currency_field='currency_id',
    )
    discount_type = fields.Selection(
        [('line', 'Order Line'), ('global', 'Global')],
        string='Discount Applies to',
        default='global',
    )
    discount_account_id = fields.Many2one(
        'account.account',
        string='Discount Account',
        compute='_compute_discount_amounts',
        store=True,
    )
    discount_amt_line = fields.Monetary(
        string='Line Discount',
        compute='_compute_discount_amounts',
        store=True,
        readonly=True,
        currency_field='currency_id',
    )
    discount_amount_line = fields.Monetary(
        string='Discount Line',
        compute='_compute_discount_amounts',
        store=True,
        readonly=True,
        currency_field='currency_id',
    )

    def _get_global_discount_amount(self, base_amount=None):
        self.ensure_one()
        base_amount = self.amount_untaxed if base_amount is None else base_amount
        if self.discount_type != 'global':
            return 0.0
        if self.discount_method == 'fix':
            return self.currency_id.round(self.discount_amount)
        if self.discount_method == 'per':
            return self.currency_id.round(base_amount * self.discount_amount / 100.0)
        return 0.0

    def _get_line_discount_amount(self):
        self.ensure_one()
        return self.currency_id.round(sum(self.invoice_line_ids.mapped('discount_amt')))

    @api.depends(
        'discount_type',
        'discount_method',
        'discount_amount',
        'invoice_line_ids.discount_amt',
        'invoice_line_ids.account_id',
        'invoice_line_ids.product_id',
        'amount_untaxed',
    )
    def _compute_discount_amounts(self):
        for move in self:
            discount_account = move.invoice_line_ids.filtered('product_id')[:1].account_id
            move.discount_account_id = discount_account

            if not move.is_sale_document(include_receipts=True):
                move.discount_amt = 0.0
                move.discount_amt_line = 0.0
                move.discount_amount_line = 0.0
                continue

            if move.discount_type == 'line':
                line_discount = move._get_line_discount_amount()
                move.discount_amt = 0.0
                move.discount_amt_line = line_discount
                move.discount_amount_line = line_discount
            else:
                move.discount_amt = move._get_global_discount_amount(move.amount_untaxed)
                move.discount_amt_line = 0.0
                move.discount_amount_line = 0.0

    def _get_discount_to_apply_on_total(self):
        self.ensure_one()
        if not self.is_sale_document(include_receipts=True):
            return 0.0
        if self.discount_type == 'line':
            return self._get_line_discount_amount()
        return self._get_global_discount_amount(self.amount_untaxed)

    def calc_discount(self):
        self._compute_discount_amounts()
        self._compute_amount()

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.balance',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id',
        'state',
        'discount_type',
        'discount_method',
        'discount_amount',
        'invoice_line_ids.discount_amt',
    )
    def _compute_amount(self):
        super()._compute_amount()
        for move in self:
            discount = move._get_discount_to_apply_on_total()
            if not discount:
                continue

            move.amount_total = move.currency_id.round(move.amount_total - discount)
            if move.move_type == 'entry':
                move.amount_total_signed = abs(move.amount_total)
                move.amount_total_in_currency_signed = abs(move.amount_total)
            else:
                move.amount_total_signed = -move.direction_sign * move.amount_total
                move.amount_total_in_currency_signed = -move.direction_sign * move.amount_total

    @api.depends(
        'invoice_line_ids.currency_rate',
        'invoice_line_ids.tax_base_amount',
        'invoice_line_ids.tax_line_id',
        'invoice_line_ids.price_total',
        'invoice_line_ids.price_subtotal',
        'invoice_payment_term_id',
        'partner_id',
        'currency_id',
        'discount_type',
        'discount_method',
        'discount_amount',
        'invoice_line_ids.discount_amt',
    )
    def _compute_tax_totals(self):
        super()._compute_tax_totals()
        for move in self:
            if not move.tax_totals:
                continue
            tax_totals = dict(move.tax_totals)
            tax_totals.update({
                'base_amount_currency': move.amount_untaxed,
                'tax_amount_currency': move.amount_tax,
                'total_amount_currency': move.amount_total,
            })
            move.tax_totals = tax_totals


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    discount_method = fields.Selection([('fix', 'Fixed'), ('per', 'Percentage')], string='Discount Method')
    discount_type = fields.Selection(related='move_id.discount_type', string='Discount Applies to')
    discount_amount = fields.Float(string='Discount Amount')
    discount_amt = fields.Monetary(
        string='Discount Final Amount',
        compute='_compute_totals',
        store=True,
        readonly=True,
        currency_field='currency_id',
    )
    flag = fields.Boolean(string='Flag')

    def _get_custom_discount_amount(self, amount=None):
        self.ensure_one()
        amount = self.currency_id.round(self.price_unit * self.quantity) if amount is None else amount
        if self.discount_type != 'line':
            return 0.0
        if self.discount_method == 'fix':
            return self.currency_id.round(self.discount_amount)
        if self.discount_method == 'per':
            return self.currency_id.round(amount * self.discount_amount / 100.0)
        return 0.0

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id', 'discount_method', 'discount_amount', 'discount_type')
    def _compute_totals(self):
        super()._compute_totals()
        AccountTax = self.env['account.tax']
        for line in self:
            line.discount_amt = 0.0
            if (
                line.display_type not in ('product', 'cogs', 'non_deductible_product', 'non_deductible_product_total')
                or not line.move_id
                or line.discount_type != 'line'
                or not line.discount_method
            ):
                continue

            gross_amount = line.currency_id.round(line.price_unit * line.quantity)
            discount = line._get_custom_discount_amount(gross_amount)
            line.discount_amt = discount

            if line.company_id.tax_discount_policy == 'untax':
                discount_percentage = gross_amount and discount / gross_amount * 100.0 or 0.0
                base_line = line.move_id._prepare_product_base_line_for_taxes_computation(line)
                base_line['discount'] = discount_percentage
                AccountTax._add_tax_details_in_base_line(base_line, line.company_id or self.env.company)
                AccountTax._round_base_lines_tax_details([base_line], line.company_id or self.env.company)
                line.price_subtotal = base_line['tax_details']['total_excluded_currency']
                line.price_total = base_line['tax_details']['total_included_currency']
            elif line.company_id.tax_discount_policy == 'tax':
                if line.discount_method == 'per':
                    line.discount_amt = line.currency_id.round(line.price_total * line.discount_amount / 100.0)
                else:
                    line.discount_amt = discount
