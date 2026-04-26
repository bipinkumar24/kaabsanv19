from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CreatePurchaseOrderWizard(models.TransientModel):
    _name = 'purchase.request.line.create.purchase.order.wizard'
    _description = 'Create Purchase Order Wizard'

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.currency_id = self.partner_id.currency_id

    @api.onchange('select_all')
    def _onchange_select_all(self):
        if self.select_all:
            self.line_ids.update({
                'select': True
            })
        elif all(self.line_ids.mapped('select')):
            self.line_ids.update({
                'select': False
            })

    @api.onchange('line_ids')
    def _onchange_line_ids(self):
        self.select_all = all(self.line_ids.mapped('select'))

    is_sync_vendor = fields.Boolean(
        string='Merge PR lines with one Supplier?', default=True,
    )
    is_required_vendor_in_pr = fields.Boolean(
        string='Required Preferred Supplier In PR?',
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier',
        domain=[('supplier_rank', '!=', 0)],
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
    )
    select_all = fields.Boolean(
        string='Select All?',
        default=True,
    )
    line_ids = fields.One2many(
        comodel_name='purchase.request.line.create.purchase.order.wizard.line',
        inverse_name='wizard_id',
        string='Lines',
    )

    def _prepare_po_values(self, partner, currency, wz_lines):
        if self.env.context.get('is_create_view'):
            request_id = self.env['purchase.request'].browse(self.env.context.get('model_data_id'))
            request_lines = request_id.line_ids.filtered(lambda x:x.rfq_create)
        else:
            request_lines = self.env['purchase.request.line'].browse(
                self._context.get('request_line_ids'))
        request_id = False
        department_id = False
        request_ids = request_lines.mapped('request_uid')
        department_ids = request_lines.mapped('department_id')
        if request_ids:
            request_id = request_ids[0]
            department_id = department_ids[0]
        return {
            'partner_id': partner.id,
            'currency_id': currency.id,
            'payment_term_id': partner.property_supplier_payment_term_id.id,
            'request_uid': request_id.id if request_id else False,
            'department_id': department_id.id if department_id else False, 
            'order_line': [
                (0, 0, line.prepare_po_line_values()) for line in wz_lines
            ]
        }

    def action_create_po_vendor_sync(self, lines):
        partner = self.partner_id
        currency = self.currency_id
        values = self._prepare_po_values(partner, currency, lines)
        order = self.env['purchase.order'].create(values)
        return {
            'name': _('Requests for Quotation'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': order.id,
            'view_mode': 'form',
        }

    def action_create_po_vendor_no_sync(self, lines):
        partners = self.env['res.partner']
        currencies = self.env['res.currency']
        for line in lines:
            if not line.partner_id:
                raise UserError(_(
                    'Please enter suppliers for all product lines. '
                    'Please check again!'
                ))
            partners |= line.partner_id
            currencies |= line.currency_id

        orders = self.env['purchase.order']
        for partner in partners:
            if len(currencies) == 1:
                currency = currencies
            else:
                currency = partner.currency_id \
                           or self.env.user.company_id.currency_id
            partner_lines = lines.filtered(
                lambda l: l.partner_id == partner)
            values = self._prepare_po_values(
                partner, currency, partner_lines)
            order = self.env['purchase.order'].create(values)
            orders |= order
        [action] = self.env.ref('purchase.purchase_rfq').read()
        action.update({
            'domain': [('id', 'in', orders.ids)],
        })
        return action

    def action_create_po(self):
        lines = self.line_ids.filtered('select')
        if self.env.context.get('is_create_view'):
            request_id = self.env['purchase.request'].browse(self.env.context.get('model_data_id'))
            purchase_request_line_ids = request_id.line_ids.filtered(lambda x:x.rfq_create)
        else:
            purchase_request_line_ids = self.env['purchase.request.line'].browse(self._context.get('request_line_ids'))

        for line in purchase_request_line_ids:
            line.write({'state_creation': 'rfq_po'})
            if line.stock_request_id:
                raise ValidationError(_('Stock Request Is Already Created for ' + line.product_id.name))
            if line.order_line_ids:
                raise ValidationError(_('Purchase RFQ/PO Is Already Created for ' + line.product_id.name))
            if line.expense_transfer_id:
                raise ValidationError(_('Expense Is Already Created for ' + line.product_id.name))

        if not lines:
            raise UserError(_(
                'Please select request lines to create RFQ/PO!'
            ))
        if self.is_sync_vendor:
            return self.action_create_po_vendor_sync(lines)
        return self.action_create_po_vendor_no_sync(lines)

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        params = self.env['ir.config_parameter'].sudo()
        is_required_vendor_in_pr = params.get_param(
            'atta_purchase_request.is_required_vendor_in_pr',
        )
        result['is_required_vendor_in_pr'] = is_required_vendor_in_pr
        if self.env.context.get('is_create_view'):
            request_id = self.env['purchase.request'].browse(self.env.context.get('model_data_id'))
            request_lines = request_id.line_ids.filtered(lambda x:x.rfq_create)
        else:
            request_lines = self.env['purchase.request.line'].browse(
                self._context.get('request_line_ids'))
        result['line_ids'] = [
            (0, 0, {
                'request_line_id': rl.id,
                'request_id': rl.request_id.id,
                'product_id': rl.product_id.id,
                'description': rl.description,
                'schedule_date': rl.schedule_date,
                'qty_to_purchase': rl.quantity,
                'purchased_qty': rl.purchased_qty,
                'quantity': rl.quantity - rl.purchased_qty,
                'partner_id': rl.partner_id.id,
                'currency_id': rl.currency_id.id,
                'uom_id': rl.uom_id.id,
                'price_unit_currency': rl.price_unit_currency,
                'price_unit': rl.price_unit,
                'tax_ids': [(6, 0, rl.tax_ids.ids)],
                'price_subtotal': rl.tax_ids.compute_all(
                    rl.price_unit,
                    rl.currency_id,
                    rl.quantity - rl.purchased_qty,
                    product=rl.product_id,
                    partner=rl.partner_id,
                )['total_excluded']
            }) for rl in request_lines
        ]

        return result


class CreatePurchaseOrderWizardLine(models.TransientModel):
    _name = 'purchase.request.line.create.purchase.order.wizard.line'
    _description = 'Create Purchase Order Wizard Line'

    @api.constrains('quantity', 'select')
    def _check_quantity(self):
        for rec in self.filtered('select'):
            if not rec.quantity > 0:
                raise ValidationError(_(
                    'Merged quantity must be greater than 0!'
                ))

    @api.depends('quantity', 'partner_id')
    def _compute_amount(self):
        for line in self:
            taxes = line.tax_ids.compute_all(
                line.price_unit,
                line.currency_id,
                line.quantity,
                product=line.product_id,
                partner=line.partner_id,
            )
            line.update({
                'price_subtotal': taxes['total_excluded'],
            })

    @api.onchange('product_id')
    def onchange_product_id(self):

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
        self.description = product_lang.display_name
        if product_lang.description_purchase:
            self.description += '\n' + product_lang.description_purchase

    @api.onchange('partner_id', 'product_id',
                  'quantity', 'uom_id', 'schedule_date')
    def _onchange_quantity(self):
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
            self.request_line_id.company_id,
        ) if seller else 0.0
        if all([
            price_unit,
            seller,
            seller.currency_id != self.currency_id,
        ]):
            price_unit = seller.currency_id._convert(
                price_unit,
                self.currency_id,
                self.request_line_id.company_id,
                self.schedule_date or fields.Date.context_today(self),
                round=False,
            )
        if all([
            seller,
            self.uom_id,
            seller.product_uom != self.uom_id,
        ]):
            price_unit = seller.product_uom._compute_price(
                price_unit,
                self.uom_id
            )

        self.price_unit_currency = price_unit

    wizard_id = fields.Many2one(
        comodel_name='purchase.request.line.create.purchase.order.wizard',
        string='wizard',
    )
    select = fields.Boolean(
        default=True,
    )
    request_line_id = fields.Many2one(
        comodel_name='purchase.request.line',
        string='Purchase Request Line',
    )
    request_id = fields.Many2one(
        comodel_name='purchase.request',
        string='Purchase Request',
        related='request_line_id.request_id',
        readonly=True,
    )
    product_id = fields.Many2one(
        related='request_line_id.product_id',
        readonly=True,
    )
    description = fields.Text(
        related='request_line_id.description',
        readonly=True,
    )
    schedule_date = fields.Datetime(
        related='request_line_id.schedule_date',
        readonly=True,
    )
    qty_to_purchase = fields.Float(
        string='Qty to Purchase',
        related='request_line_id.quantity',
        readonly=True,
    )
    purchased_qty = fields.Float(
        string='Qty in RFQ/PO',
        related='request_line_id.purchased_qty',
        readonly=True,
    )
    quantity = fields.Float(
        string='Qty to Create RFQ/PO',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Preferred Supplier',
        domain=[('supplier_rank', '!=', 0)],
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
    )
    uom_id = fields.Many2one(
        related='request_line_id.uom_id',
        readonly=True,
    )
    price_unit_currency = fields.Float(
        related='request_line_id.price_unit_currency',
        readonly=True,
    )
    price_unit = fields.Float(
        related='request_line_id.price_unit',
        readonly=True,
    )
    tax_ids = fields.Many2many(
        related='request_line_id.tax_ids',
        readonly=True,
    )
    price_subtotal = fields.Float(
        string='Subtotal',
        readonly=True,
        compute='_compute_amount',
    )

    def prepare_po_line_values(self):
        return {
            'product_id': self.product_id.id,
            'name': self.description,
            'date_planned': self.schedule_date,
            'product_qty': self.quantity,
            'product_uom': self.uom_id.id,
            'price_unit': self.price_unit_currency,
            'taxes_id': [(6, 0, self.tax_ids.ids)],
            'request_line_id': self.request_line_id.id,
        }
