# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
################################################################################


from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.depends('list_price', 'standard_price')
    def _calc_margin(self):
        for product in self:
            ans = 0
            if product.list_price == 0 or product.standard_price == 0:
                ans = 0
            else:
                ans = ((product.list_price - product.standard_price) / product.list_price) * 100
            product.margin = ans
                           
    margin = fields.Float('Margin %', compute='_calc_margin', readonly=True)
