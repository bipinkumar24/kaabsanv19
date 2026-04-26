# -*- coding: utf-8 -*-
from odoo import models, fields, api, _




# Odoo 19 migration: stock.valuation.layer is no longer a live model in this codebase.
# The old code is kept below for migration reference and is intentionally not loaded.
#
# class StockValuationLayer(models.Model):
#     _inherit = 'stock.valuation.layer'
#
#     def _validate_accounting_entries(self):
#         am_vals = []
#         account_moves = self.env['account.move']
#         move_ids = False
#         for svl in self:
#             if not svl.with_company(svl.company_id).product_id.valuation == 'real_time':
#                 continue
#             if svl.currency_id.is_zero(svl.value):
#                 continue
#             am_vals += svl.stock_move_id.with_company(svl.company_id)._account_entry_move(svl.quantity, svl.description, svl.id, svl.value)
#             move_ids = svl.stock_move_id.account_move_ids.filtered(lambda x: x.state == 'draft')
#         if am_vals and not move_ids:
#             account_moves = self.env['account.move'].sudo().create(am_vals)
#             # account_moves._post()
#         for svl in self:
#             # Eventually reconcile together the invoice and valuation accounting entries on the stock interim accounts
#             if svl.company_id.anglo_saxon_accounting:
#                 svl.stock_move_id._get_related_invoices()._stock_account_anglo_saxon_reconcile_valuation(product=svl.product_id)
#         # if account_moves:
#         #     account_moves.button_draft()
