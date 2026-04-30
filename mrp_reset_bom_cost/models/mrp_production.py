# -*- coding: utf-8 -*-

import logging

from odoo import SUPERUSER_ID, models

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def button_mark_done(self):
        self = self.with_user(SUPERUSER_ID)
        self.sudo().product_id.button_bom_cost()
        # Refresh BOM cost for component products that also have their own BOMs.
        for line in self.move_raw_ids:
            if line.product_id.bom_ids:
                line.product_id.button_bom_cost()
        return super().button_mark_done()


# Odoo 19 removed the old stock.valuation.layer model. Keep the legacy logic
# commented for reference; importing this _inherit crashes registry loading.
# class StockValuationLayer(models.Model):
#     _inherit = "stock.valuation.layer"
#
#     def _update_journal_entries(self):
#         self = self.with_user(SUPERUSER_ID)
#         for valuation in self:
#             if (
#                 valuation.account_move_id
#                 and "MO" not in valuation.description
#                 and valuation.quantity > 0
#                 and valuation.valuation_unit_price < 0
#             ):
#                 for line in valuation.account_move_id.line_ids:
#                     if line.credit > 0:
#                         postive = False
#                         if valuation.stock_move_id.production_id.product_id.id == valuation.product_id.id:
#                             postive = True
#                         elif valuation.stock_move_id.picking_type_id.code == "incoming":
#                             postive = True
#                         elif valuation.stock_move_id.picking_type_id.code == "outgoing":
#                             postive = False
#                         amount_currency = line.amount_currency or 0.0
#                         quantity = valuation.quantity or 0.0
#
#                         if quantity != 0.0:
#                             price = abs(amount_currency) / abs(quantity)
#                             if postive:
#                                 valuation.sudo().write({"unit_cost": price, "value": abs(amount_currency)})
#                             else:
#                                 valuation.sudo().write({"unit_cost": price, "value": -abs(amount_currency)})


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # If any debit or credit values are updated, and this journal entry is linked to a valuation,
    # The product price and total amount in the valuation will also be updated accordingly.

    def write(self, values):
        self = self.with_user(SUPERUSER_ID)
        res = super().write(values)

        # Odoo 19 no longer exposes stock.valuation.layer. Legacy valuation
        # correction code is kept commented for migration reference.
        # if "credit" in values:
        #     move_id = self.move_id
        #     valuation = self.env["stock.valuation.layer"].sudo().search([
        #         ("account_move_id", "=", move_id.id)
        #     ], limit=1)
        #
        #     if valuation:
        #         postive = False
        #         try:
        #             if valuation.stock_move_id.production_id.product_id.id == valuation.product_id.id:
        #                 postive = True
        #             elif valuation.stock_move_id.picking_type_id.code == "incoming":
        #                 postive = True
        #             elif valuation.stock_move_id.picking_type_id.code == "outgoing":
        #                 postive = False
        #
        #             amount_currency = values.get("amount_currency")
        #             quantity = valuation.quantity
        #
        #             if amount_currency is not None and quantity:
        #                 price = abs(amount_currency) / abs(quantity)
        #                 val_dict = {
        #                     "unit_cost": price,
        #                     "value": abs(amount_currency) if postive else -abs(amount_currency),
        #                 }
        #                 valuation.sudo().write(val_dict)
        #             else:
        #                 _logger.warning(
        #                     "Skipping valuation update: amount_currency=%s, quantity=%s",
        #                     amount_currency, quantity
        #                 )
        #
        #         except Exception as e:
        #             _logger.error("Error updating stock valuation layer: %s", str(e), exc_info=True)

        return res
