# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    purchase_price = fields.Float(string='Cost', compute='_compute_purchase_price', digits='Product Price')

    @api.depends('total_cost', 'qty')
    def _compute_purchase_price(self):
        for line in self:
            line.purchase_price = line.qty and line.total_cost / line.qty or 0.0
