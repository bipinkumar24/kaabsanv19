# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_fual_expense = fields.Boolean(string="Is Fual Expense Location")

    @api.constrains('is_fual_expense', 'usage')
    def _check_vendor_lead_time(self):
        for rec in self:
            if rec.is_fual_expense:
                if rec.usage != 'inventory':
                    raise ValidationError(_("You can select only inventory loss location"))
