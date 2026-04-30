# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
################################################################################

from odoo import api, fields, models

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    line_margin = fields.Float(
        string='Margin',
        digits='Account',
        store=True,
        readonly=True,
        compute='_calc_margin',
    )


    @api.depends('price_unit', 'product_uom_qty', 'tax_ids', 'product_id', 'order_id.partner_id', 'order_id.currency_id')
    def _calc_margin(self):
        for res in self:
            cost = (res.purchase_price or res.product_id.standard_price) * res.product_uom_qty
            res.line_margin = res.price_subtotal - cost


    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res.update({'purchase_price': self.purchase_price})
        return res


class SaleOrder(models.Model):
    _inherit = "sale.order"

    margin_cust = fields.Float('Margin %', compute='_calc_margin', readonly=True)
    margin_calc = fields.Float('Margin', compute='_calc_margin', readonly=True)

    @api.depends('order_line.line_margin', 'amount_untaxed')
    def _calc_margin(self):
        for order in self:
            margin = sum(order.order_line.mapped('line_margin'))
            if order.amount_untaxed:
                order.margin_cust = (margin * 100) / order.amount_untaxed
                order.margin_calc = margin
            else:
                order.margin_cust = 0.0
                order.margin_calc = 0.0
