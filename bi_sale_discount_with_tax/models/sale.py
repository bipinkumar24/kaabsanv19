# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    discount_method = fields.Selection([('fix', 'Fixed'), ('per', 'Percentage')], string='Discount Method')
    discount_amount = fields.Float(string='Discount Amount')
    discount_amt = fields.Monetary(
        string='Discount',
        compute='_compute_amounts',
        store=True,
        readonly=True,
    )
    discount_type = fields.Selection(
        [('line', 'Order Line'), ('global', 'Global')],
        string='Discount Applies to',
        default='global',
    )
    discount_amt_line = fields.Monetary(
        string='Line Discount',
        compute='_compute_amounts',
        store=True,
        readonly=True,
    )

    def _get_global_discount_amount(self, base_amount=None):
        self.ensure_one()
        base_amount = self.amount_untaxed if base_amount is None else base_amount
        if self.discount_type != 'global':
            return 0.0
        if self.discount_method == 'fix':
            return self.currency_id.round(self.discount_amount)
        if self.discount_method == 'per':
            return self.currency_id.round(base_amount * self.discount_amount / 100.0)
        return 0.0

    def _get_line_discount_amount(self):
        self.ensure_one()
        return self.currency_id.round(sum(self.order_line.mapped('discount_amt')))

    @api.depends(
        'order_line.price_subtotal',
        'order_line.price_tax',
        'order_line.discount_amt',
        'currency_id',
        'company_id',
        'payment_term_id',
        'discount_method',
        'discount_amount',
        'discount_type',
    )
    def _compute_amounts(self):
        super()._compute_amounts()
        for order in self:
            if order.discount_type == 'line':
                discount = order._get_line_discount_amount()
                order.discount_amt = 0.0
                order.discount_amt_line = discount
            else:
                discount = order._get_global_discount_amount(order.amount_untaxed)
                order.discount_amt = discount
                order.discount_amt_line = 0.0

            if discount and order.company_id.tax_discount_policy == 'tax':
                order.amount_total = order.currency_id.round(order.amount_untaxed + order.amount_tax - discount)

    @api.depends_context('lang')
    @api.depends(
        'order_line.price_subtotal',
        'order_line.price_tax',
        'order_line.discount_amt',
        'currency_id',
        'company_id',
        'payment_term_id',
        'discount_method',
        'discount_amount',
        'discount_type',
    )
    def _compute_tax_totals(self):
        super()._compute_tax_totals()
        for order in self:
            if not order.tax_totals:
                continue
            tax_totals = dict(order.tax_totals)
            tax_totals.update({
                'base_amount_currency': order.amount_untaxed,
                'tax_amount_currency': order.amount_tax,
                'total_amount_currency': order.amount_total,
            })
            order.tax_totals = tax_totals

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        res.update({
            'discount_method': self.discount_method,
            'discount_amount': self.discount_amount,
            'discount_amt': self.discount_amt,
            'discount_type': self.discount_type,
            'discount_amt_line': self.discount_amt_line,
            'discount_amount_line': self.discount_amt_line,
        })
        return res

    def _create_invoices(self, grouped=False, final=False, date=None):
        invoices = super()._create_invoices(grouped=grouped, final=final, date=date)
        for invoice in invoices:
            sale_orders = invoice.invoice_line_ids.sale_line_ids.order_id
            if not sale_orders:
                continue
            sale_order = sale_orders[:1]
            invoice.discount_type = sale_order.discount_type
            invoice.discount_method = sale_order.discount_method
            invoice.discount_amount = sale_order.discount_amount
            invoice.discount_amt = sale_order.discount_amt
            invoice.discount_amt_line = sale_order.discount_amt_line
            invoice.discount_amount_line = sale_order.discount_amt_line
        return invoices


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_apply_on_discount_amount = fields.Boolean(string='Tax Apply After Discount')
    discount_method = fields.Selection([('fix', 'Fixed'), ('per', 'Percentage')], string='Discount Method')
    discount_type = fields.Selection(related='order_id.discount_type', string='Discount Applies to')
    discount_amount = fields.Float(string='Discount Amount')
    discount_amt = fields.Monetary(
        string='Discount Final Amount',
        compute='_compute_amount',
        store=True,
        readonly=True,
        currency_field='currency_id',
    )

    def _get_custom_discount_amount(self, amount=None):
        self.ensure_one()
        amount = self.currency_id.round(self.price_unit * self.product_uom_qty) if amount is None else amount
        if self.discount_type != 'line':
            return 0.0
        if self.discount_method == 'fix':
            return self.currency_id.round(self.discount_amount)
        if self.discount_method == 'per':
            return self.currency_id.round(amount * self.discount_amount / 100.0)
        return 0.0

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_ids', 'discount_method', 'discount_amount', 'discount_type')
    def _compute_amount(self):
        super()._compute_amount()
        AccountTax = self.env['account.tax']
        for line in self:
            line.discount_amt = 0.0
            if line.display_type or line.discount_type != 'line' or not line.discount_method:
                continue

            gross_amount = line.currency_id.round(line.price_unit * line.product_uom_qty)
            discount = line._get_custom_discount_amount(gross_amount)
            line.discount_amt = discount

            if line.company_id.tax_discount_policy == 'untax':
                discount_percentage = gross_amount and discount / gross_amount * 100.0 or 0.0
                base_line = line._prepare_base_line_for_taxes_computation(discount=discount_percentage)
                AccountTax._add_tax_details_in_base_line(base_line, line.company_id or self.env.company)
                AccountTax._round_base_lines_tax_details([base_line], line.company_id or self.env.company)
                line.price_subtotal = base_line['tax_details']['total_excluded_currency']
                line.price_total = base_line['tax_details']['total_included_currency']
                line.price_tax = line.price_total - line.price_subtotal

            elif line.company_id.tax_discount_policy == 'tax':
                if line.discount_method == 'per':
                    line.discount_amt = line.currency_id.round(line.price_total * line.discount_amount / 100.0)
                else:
                    line.discount_amt = discount

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        res.update({
            'discount': self.discount,
            'discount_method': self.discount_method,
            'discount_amount': self.discount_amount,
            'discount_amt': self.discount_amt,
        })
        return res


class ResCompany(models.Model):
    _inherit = 'res.company'

    tax_discount_policy = fields.Selection(
        [('tax', 'Tax Amount'), ('untax', 'Untax Amount')],
        string='Discount Applies On',
        default='tax',
    )


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tax_discount_policy = fields.Selection(
        related='company_id.tax_discount_policy',
        readonly=False,
        string='Discount Applies On',
    )
