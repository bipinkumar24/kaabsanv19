from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

from .purchase_request import PO_CREATION_STATE_SELECTION


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'
    is_first = fields.Boolean('Is first', compute='_compute_is_first')

    @api.depends('next_approval_id')
    def _compute_is_first(self):
        for rec in self:
            if rec.next_approval_id.level == 1:
                rec.is_first = True
            else:
                rec.is_first = False
     
    def search(self, args, **kwargs):
        if self.env.user.has_group('expense_requests.can_request_expenses'):
            args += [('create_uid', '=', self.env.user.id)]
        if self.env.user.has_group('expense_requests.expensess_manager'):
            args += ['|',('create_uid.department_id', '=', self.env.user.department_id.id),
                     ('create_uid.department_id', 'child_of', self.env.user.department_id.id)]
        if self.env.user.has_group('expense_requests.all_expensess_manager'):
            args += [(1, '=', 1)]

        return super(PurchaseRequest, self).search(args, **kwargs)

class PurchaseRequestLine(models.Model):
    _name = 'purchase.request.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Purchase Request Line'
    _order = 'id desc'

    @api.constrains('request_qty')
    def _check_request_qty(self):
        for rec in self:
            if not rec.request_qty > 0:
                field_request_qty_string = self.fields_get(
                    ['request_qty'], ['string']
                )['request_qty']['string']
                raise ValidationError(_(
                    '%s must be greater than 0!'
                ) % field_request_qty_string)

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity < 0:
                field_quantity_string = self.fields_get(
                    ['quantity'], ['string']
                )['quantity']['string']
                raise ValidationError(_(
                    '%s must not be less than 0!'
                ) % field_quantity_string)
                
                
    def search(self, args, **kwargs):
        if self.env.user.has_group('expense_requests.can_request_expenses'):
            args += [('create_uid', '=', self.env.user.id)]
        if self.env.user.has_group('expense_requests.expensess_manager'):
            args += ['|',('create_uid.department_id', '=', self.env.user.department_id.id),
                     ('create_uid.department_id', 'child_of', self.env.user.department_id.id)]
        if self.env.user.has_group('expense_requests.all_expensess_manager'):
            args += [(1, '=', 1)]

        return super(PurchaseRequestLine, self).search(args, **kwargs)
        
    @api.depends(
        'currency_id',
        'request_currency_id',
        'price_unit_currency',
        'request_id.currency_rate_ids.currency_id',
        'request_id.currency_rate_ids.rate',
    )
    def _compute_price_unit(self):
        for rec in self:
            rec.price_unit = rec.price_unit_currency
            rates = rec.request_id.currency_rate_ids
            if not rates:
                continue
            company_rate = rates.filtered(
                lambda r: r.currency_id == rec.request_currency_id
            ).rate or 1
            request_line_rate = rates.filtered(
                lambda r: r.currency_id == rec.currency_id
            ).rate or 1
            rate = company_rate / request_line_rate
            rec.price_unit = rec.price_unit_currency * rate

    @api.depends('quantity', 'price_unit', 'tax_ids',
                 'currency_id', 'partner_id')
    def _compute_amount(self):
        for line in self:
            taxes = line.tax_ids.compute_all(
                line.price_unit,
                line.request_currency_id,
                line.quantity,
                product=line.product_id,
                partner=line.partner_id,
            )
            price_tax = sum(
                t.get('amount', 0.0) for t in taxes.get('taxes', [])
            )
            line.update({
                'price_tax': price_tax,
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.depends(
        'order_line_ids.order_id.state',
        'order_line_ids.product_qty',
    )
    def _compute_purchased_qty(self):
        for rec in self:
            rec.purchased_qty = 0
            order_lines = rec.order_line_ids.filtered(
                lambda ol: ol.order_id.state != 'cancel')
            if order_lines:
                rec.purchased_qty = sum(order_lines.mapped('product_qty'))

    @api.depends('purchased_qty', 'quantity')
    def _compute_po_creation_state(self):
        for rec in self:
            if rec.purchased_qty == 0:
                rec.po_creation_state = 'not'
            elif rec.purchased_qty < rec.quantity:
                rec.po_creation_state = 'partially'
            else:
                rec.po_creation_state = 'fully'

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.tax_ids = self.product_id.supplier_taxes_id
        if not self.product_id:
            return

        self.uom_id = self.product_id.uom_po_id
        order_line = self.env['purchase.order.line'].sudo().search(
            [
                ('product_id', '=', self.product_id.id),
                ('state', 'in', ['purchase', 'done']),
            ],
            limit=1,
            order='date_order desc',
        )

        self.partner_id = order_line.partner_id
        if order_line:
            self.currency_id = order_line.currency_id

    @api.onchange('product_id', 'partner_id')
    def onchange_product_and_partner(self):
        if not self.product_id:
            return

        product_lang = self.product_id.with_context(
            lang=self.partner_id.lang,
            partner_id=self.partner_id.id,
        )
        if product_lang.description_purchase:
            self.description += '\n' + product_lang.description_purchase

    @api.onchange('request_qty')
    def onchange_request_qty(self):
        self.quantity = self.request_qty

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        vendor_lead_time = self.partner_id.vendor_lead_time
        if not vendor_lead_time:
            return
        now = fields.Datetime.now()
        date_to_calculate = now
        schedule_date = fields.Datetime.to_string(
            date_to_calculate + timedelta(days=vendor_lead_time))
        self.schedule_date = schedule_date

    @api.onchange('partner_id', 'product_id',
                  'quantity', 'uom_id', 'schedule_date')
    def onchange_quantity(self):
        if not self.product_id:
            return

        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.quantity,
            date=self.schedule_date or fields.Date.today(),
            uom_id=self.uom_id,
        )

        if not seller:
            return

        price_unit = self.env['account.tax']._fix_tax_included_price_company(
            seller.price,
            self.product_id.supplier_taxes_id,
            self.tax_ids,
            self.company_id,
        ) if seller else 0.0
        if all([
            price_unit,
            seller,
            seller.currency_id != self.currency_id,
        ]):
            price_unit = seller.currency_id._convert(
                price_unit,
                self.currency_id,
                self.company_id,
                self.schedule_date or fields.Date.context_today(self),
                round=False,
            )
        if all([
            seller,
            self.uom_id,
            seller.product_uom_id != self.uom_id,
        ]):
            price_unit = seller.product_uom_id._compute_price(
                price_unit,
                self.uom_id
            )

        self.price_unit_currency = price_unit

    is_first = fields.Boolean('Is button', compute='_compute_is_first')

    @api.depends('request_id')
    def _compute_is_first(self):
        for rec in self:
            rec.is_first = rec.request_id.is_first

    request_id = fields.Many2one(
        comodel_name='purchase.request',
        string='Purchase Request',
        required=True,
        index=True,
        ondelete='cascade',
    )

    request_state = fields.Selection(
        related='request_id.state',
        string='Purchase Request Status',
        readonly=True,
        store=True,
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        domain=[
            ('purchase_ok', '=', True),
        ],
        tracking=True,
    )
    description = fields.Text(
        required=True,
        tracking=True,
    )

    request_deliver_date = fields.Date(
        string='Requested Delivery Date',
        required=True,
    )
    schedule_date = fields.Datetime(
        string='Scheduled Date',
        tracking=True,
    )

    request_qty = fields.Float(
        string='Requested Qty',
        required=True,
        default=1,
        tracking=True,
    )
    quantity = fields.Float(
        string='Qty to Purchase',
        required=True,
        tracking=True,
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Preferred Vendor',
        domain=[('supplier_rank', '!=', 0)],
        tracking=True,
    )

    company_id = fields.Many2one(
        related='request_id.company_id',
        store=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.user.company_id.currency_id.id,
        tracking=True,
    )
    request_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Request Currency',
        related='request_id.currency_id',
        readonly=True,
        store=True,
    )
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        required=True,
    )
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        string='Taxes',
        domain=[('type_tax_use', '=', 'purchase')],
    )
    price_unit_currency = fields.Float(
        string='Unit Price (FCY)',
        required=True,
        digits='Product Price',
        tracking=True,
        default=0,
    )
    price_unit = fields.Float(
        string='Unit Price (CCY)',
        readonly=True,
        digits='Product Price',
        compute='_compute_price_unit',
        store=True,
    )
    price_subtotal = fields.Float(
        string='Subtotal',
        readonly=True,
        compute='_compute_amount',
        store=True,
    )
    price_total = fields.Float(
        string='Total',
        readonly=True,
        compute='_compute_amount',
        store=True,
    )
    price_tax = fields.Float(
        string='Tax',
        readonly=True,
        compute='_compute_amount',
        store=True,
    )

    note = fields.Text(
        string='Notes',
    )

    order_line_ids = fields.One2many(
        comodel_name='purchase.order.line',
        inverse_name='request_line_id',
        string='Purchase Order Lines',
        readonly=True,
    )
    purchased_qty = fields.Float(
        string='Quantity in RFQ or PO',
        readonly=True,
        compute='_compute_purchased_qty',
        compute_sudo=True,
        store=True,
    )
    po_creation_state = fields.Selection(
        selection=PO_CREATION_STATE_SELECTION,
        string='RFQ/PO Creation Status',
        compute='_compute_po_creation_state',
        store=True,
    )

    state_creation = fields.Selection([('not', 'Not Created'),
                                       ('rfq_po', 'RFQ/PO Created'),
                                       ('expense', 'Expense Transfer Created'),
                                       ('stock', 'Stock Request Created')],
                                      default='not',
                                      string='Creation Status')

    is_edited = fields.Boolean(
        default=True,
    )
    expense_transfer_id = fields.Many2one('stock.picking', string='Expense Transfer')
    stock_request_id = fields.Many2one('stock.request', string='Stock Request')
    request_uid = fields.Many2one(
        related='request_id.create_uid',
        string='Requester',
        readonly=True,
        store=True,
    )
    department_id = fields.Many2one(
        related='request_id.department_id',
        string='Department',
        readonly=True,
        store=True,
    )
    is_allocation = fields.Boolean(string="Is Allocation")
    is_expense = fields.Boolean(string="Is Expense")
    rfq_create = fields.Boolean(string="Rfq")
    allocation_create = fields.Boolean(string="Allocation")
    expense_create = fields.Boolean(string="Expense")

    def create_expense_transfer(self):
        messages = []
        not_final_requests = self.mapped('request_id').filtered(
            lambda r: r.state != 'final')
        if not_final_requests:
            for request in not_final_requests:
                message = _(
                    'Purchase Request %s is not approved!'
                ) % request.name
                messages.append(message)
        return {
            'name': _('Create Expense Transfer'),
            'type': 'ir.actions.act_window',
            'res_model': 'expense.transfer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'request_line_ids': self.ids,
            },
        }

    def create_stock_request(self):
        messages = []
        not_final_requests = self.mapped('request_id').filtered(
            lambda r: r.state != 'final')
        if not_final_requests:
            for request in not_final_requests:
                message = _(
                    'Purchase Request %s is not approved!'
                ) % request.name
                messages.append(message)
        return {
            'name': _('Create Stock Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'request_line_ids': self.ids,
            },
        }

    def create_purchase_order(self):
        messages = []
        not_final_requests = self.mapped('request_id').filtered(
            lambda r: r.state != 'final')
        if not_final_requests:
            for request in not_final_requests:
                message = _(
                    'Purchase Request %s is not approved!'
                ) % request.name
                messages.append(message)

        fully_lines = self.filtered(lambda l: l.po_creation_state == 'fully')
        if fully_lines:
            messages.append(_(
                'There are products that have been fully created RFQ/PO. '
                'Please check again!'
            ))

        quantity_zero_lines = self.filtered(lambda l: l.quantity == 0)
        if quantity_zero_lines:
            messages.append(_(
                'There are products whose quantity can be '
                'purchased equal to 0. Please check again!'
            ))

        if messages:
            raise UserError('\n'.join(messages))

        return {
            'name': _('Create RFQ/PO'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.request.line.create.purchase.order.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'request_line_ids': self.ids,
            },
        }

    def check_state_for_changing_lines(self):
        self.ensure_one()
        if self.request_id.state != 'draft':
            raise UserError(_(
                'You cannot add/delete request lines when '
                'purchase request status is difference from draft!'
            ))

    @api.model
    def create(self, values):
        res = super(PurchaseRequestLine, self).create(values)
        res.check_state_for_changing_lines()
        return res

    def unlink(self):
        for rec in self:
            rec.check_state_for_changing_lines()
        return super(PurchaseRequestLine, self).unlink()

    def name_get(self):
        return [
            (
                rec.id,
                '{pr} / {product}'.format(
                    pr=rec.request_id.name,
                    product=rec.product_id.display_name,
                )
            ) for rec in self
        ]
