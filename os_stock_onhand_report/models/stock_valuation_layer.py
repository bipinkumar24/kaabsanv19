# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    cost = fields.Float(string='Cost', digits=(16, 4), compute="_compute_account_move_line_cost", store=True)

    @api.depends('amount_currency', 'quantity')
    def _compute_account_move_line_cost(self):
        for rec in self:
            if rec.amount_currency and rec.quantity:
                rec.cost = rec.amount_currency / rec.quantity
            else:
                rec.cost = 0.0


class StockMove(models.Model):
    _inherit = 'stock.move'

    # stock.valuation.layer was removed in Odoo 19.
    # Valuation is now stored directly on stock.move via 'value' (total) and 'price_unit'.
    valuation_unit_price = fields.Float(
        string="Valuation Unit Price",
        compute="_compute_valuation_unit_price",
        store=True,
        digits=(16, 4),
    )

    @api.depends('value', 'quantity')
    def _compute_valuation_unit_price(self):
        for move in self:
            if move.quantity:
                move.valuation_unit_price = abs(move.value / move.quantity)
            else:
                move.valuation_unit_price = 0.0

    def action_update_unit_price(self):
        for move in self:
            if move.quantity:
                move.valuation_unit_price = abs(move.value / move.quantity)
            else:
                move.valuation_unit_price = 0.0

            # For inventory adjustments derive unit price from the linked account move
            if move.account_move_id and (
                'Inventory Adjustment' in (move.reference or '')
                or 'Product Quantity Updated' in (move.reference or '')
            ):
                total_credit = move.account_move_id.line_ids.mapped('credit')
                if total_credit and move.product_uom_qty:
                    move.valuation_unit_price = total_credit[0] / move.product_uom_qty

    def action_add_journal_entries(self):
        return {
            'name': 'Add Journal Entries',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'link.journal.entry.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_move_id': self.id},
        }
