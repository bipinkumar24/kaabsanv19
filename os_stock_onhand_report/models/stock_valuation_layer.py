# -*- coding: utf-8 -*-
from odoo import api, fields, models

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    cost = fields.Float(string="Cost", digits=(16, 4), compute="_compute_account_move_line_cost", store=True)

    @api.depends("amount_currency", "quantity")
    def _compute_account_move_line_cost(self):
        for rec in self:
            if rec.amount_currency and rec.quantity:
                rec.cost = rec.amount_currency / rec.quantity
            else:
                rec.cost = 0.0


# Odoo 19 no longer exposes stock.valuation.layer and related move fields.
# Keep this legacy code commented so importing this file cannot crash registry.
# class StockValuationLayer(models.Model):
#     _inherit = "stock.valuation.layer"
#
#     valuation_unit_price = fields.Float(string="Valuation Unit Price", compute="_compute_valuation_unit_price", store=True, digits=(16, 4))
#
#     @api.depends("value", "quantity")
#     def _compute_valuation_unit_price(self):
#         for valuation in self:
#             if valuation.quantity != 0:
#                 valuation.valuation_unit_price = valuation.value / valuation.quantity
#             else:
#                 valuation.valuation_unit_price = 0.0
#
#     def action_update_unit_price(self):
#         for valuation in self:
#             if valuation.quantity != 0:
#                 valuation.valuation_unit_price = abs(valuation.value / valuation.quantity)
#             else:
#                 valuation.valuation_unit_price = 0.0
#
# class StockMove(models.Model):
#     _inherit = "stock.move"
#
#     valuation_unit_price = fields.Float(string="Valuation Unit Price", compute="_compute_valuation_unit_price", store=True, digits=(16, 4))
#
#     @api.depends("stock_valuation_layer_ids", "stock_valuation_layer_ids.valuation_unit_price")
#     def _compute_valuation_unit_price(self):
#         for valuation in self:
#             prices = valuation.stock_valuation_layer_ids.mapped("valuation_unit_price")
#             if prices:
#                 valuation.valuation_unit_price = max(prices)
#             else:
#                 valuation.valuation_unit_price = 0.0
#
#
#     def action_update_unit_price(self):
#         for valuation in self:
#             prices = valuation.stock_valuation_layer_ids.mapped("valuation_unit_price")
#             if prices:
#                 valuation.valuation_unit_price = max(prices)
#             else:
#                 valuation.valuation_unit_price = 0.0
#             if "Inventory Adjustment" in valuation.reference or "Product Quantity Updated" in valuation.reference:
#                 account_move_id = self.env["account.move"].search([("stock_move_id", "=", valuation.id)])
#                 if account_move_id:
#                     total_credit = account_move_id.line_ids.mapped("credit")
#                     if total_credit:
#                         valuation.valuation_unit_price = total_credit[0] / valuation.product_uom_qty
#
#
#     def action_add_journal_entries(self):
#         return {
#             "name": "Add Journal Entries",
#             "view_mode": "form",
#             "res_model": "link.journal.entry.wizard",
#             "type": "ir.actions.act_window",
#             "target": "new",
#             "context": {
#                 "default_move_id": self.id,
#             },
#         }
