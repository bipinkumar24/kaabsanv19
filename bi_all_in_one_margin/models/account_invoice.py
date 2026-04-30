# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
################################################################################

from odoo import api, fields, models

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    line_margin = fields.Float(string='Margin', digits='Account', store=True, readonly=True, compute='_calc_margin')
    purchase_price = fields.Float('Cost', compute='_get_product_cost', digits='Product Price', store=True)
    margin_subtotal_signed = fields.Float(string='Margin Signed', readonly=True, store=True, compute='_calc_margin')

    @api.depends('product_id', 'product_uom_id', 'move_id.currency_id', 'move_id.company_id')
    def _get_product_cost(self):
        for line in self:
            if not line.product_id:
                line.purchase_price = 0.0
                continue
            company = line.move_id.company_id or line.env.company
            from_currency = company.currency_id
            to_currency = line.move_id.currency_id or from_currency
            purchase_price = line.product_id.standard_price
            if line.product_id.uom_id and line.product_uom_id and line.product_uom_id != line.product_id.uom_id:
                purchase_price = line.product_id.uom_id._compute_price(purchase_price, line.product_uom_id)
            line.purchase_price = from_currency._convert(
                purchase_price,
                to_currency,
                company,
                line.move_id.invoice_date or fields.Date.today(),
                round=False,
            )

    @api.depends('price_unit', 'discount', 'tax_ids', 'quantity',
                 'product_id', 'move_id.partner_id', 'move_id.currency_id')
    def _calc_margin(self):
        for res in self:
            cost = (res.purchase_price or res.product_id.standard_price) * res.quantity
            margin = res.price_subtotal - cost
            res.line_margin = margin
            sign = res.move_id.move_type in ['in_refund', 'out_refund'] and -1 or 1
            res.margin_subtotal_signed = margin * sign

    
class AccountMove(models.Model):
    _inherit = "account.move"

    margin_cust = fields.Float('Margin %', compute='_calc_margin')
    margin_calc = fields.Float('Margin', compute='_calc_margin')
    
    @api.depends('invoice_line_ids.line_margin', 'amount_untaxed')
    def _calc_margin(self): 
        for order in self:
            margin = sum(order.invoice_line_ids.mapped('line_margin'))
            if order.amount_total and order.amount_untaxed:
                order.margin_cust = (margin * 100) / order.amount_untaxed
                order.margin_calc = margin
            else:
                order.margin_cust = 0.0
                order.margin_calc = 0.0

