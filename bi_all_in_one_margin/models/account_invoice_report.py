# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
################################################################################

from odoo import api, fields, models
from odoo.addons.account.report.account_invoice_report import AccountInvoiceReport as BaseAccountInvoiceReport
from odoo.tools import SQL

class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    margin_subtotal_signed = fields.Float('Margin')
    _depends = {
        **BaseAccountInvoiceReport._depends,
        'account.move.line': BaseAccountInvoiceReport._depends['account.move.line'] + ['margin_subtotal_signed'],
    }

    @api.model
    def _select(self) -> SQL:
        return SQL('%s, line.margin_subtotal_signed AS margin_subtotal_signed', super()._select())
