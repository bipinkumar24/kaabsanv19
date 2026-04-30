# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


# Odoo 19 no longer exposes stock.valuation.layer. Keep this legacy code
# commented so importing this file cannot crash the registry.
# class StockValuationLayer(models.Model):
#     _inherit = 'stock.valuation.layer'

#     def _validate_accounting_entries(self):
#         am_vals = []
#         account_moves = self.env['account.move']
#         for svl in self:
#             if not svl.with_company(svl.company_id).product_id.valuation == 'real_time':
#                 continue
#             if svl.currency_id.is_zero(svl.value):
#                 continue
#             am_vals += svl.stock_move_id.with_company(svl.company_id)._account_entry_move(svl.quantity, svl.description, svl.id, svl.value)
#         if am_vals:
#             account_moves = self.env['account.move'].sudo().create(am_vals)
#             # account_moves._post()
#         for svl in self:
#             # Eventually reconcile together the invoice and valuation accounting entries on the stock interim accounts
#             if svl.company_id.anglo_saxon_accounting:
#                 svl.stock_move_id._get_related_invoices()._stock_account_anglo_saxon_reconcile_valuation(product=svl.product_id)
#         # if account_moves:
#         #     account_moves.button_draft()
