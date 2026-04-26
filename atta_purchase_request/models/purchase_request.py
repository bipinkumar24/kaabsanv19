from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

DEFAULT_NAME = _('New')

STATE = [
    ('draft', 'Draft'),
    ('first', 'Dept. Approval'),
    ('second', 'Site Manager'),
    ('third', 'Operation Approval'),
    ('fourth', 'GM Approval'),
    ('final', 'To Purchase'),
    ('done', 'Locked'),
    ('canceled', 'Canceled'),
]

PO_CREATION_STATE_SELECTION = [
    ('not', 'Not Created'),
    ('partially', 'Partially Created'),
    ('fully', 'Fully Created'),
]


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Purchase Request'
    _order = 'id desc'

    @api.depends('next_approval_id', 'next_approval_id.approval_user_ids')
    def _compute_next_approval_user_id(self):
        for rec in self:
            rec.next_approval_user_ids = [(6, 0, rec.next_approval_id.approval_user_ids.ids)]

    @api.depends('next_approval_id', 'next_approval_user_ids')
    def _compute_is_button(self):
        for rec in self:
            if self.env.user.id in rec.next_approval_user_ids.ids:
                rec.is_button = True
            else:
                rec.is_button = False

            if rec.next_approval_id.is_full_field or rec.next_approval_id.is_reject:
                rec.is_button = False
            if rec.next_approval_id.is_last_approval:
                rec.is_last_level = True
                rec.state = 'final'
            else:
                rec.is_last_level = False

    def _get_next_approval_id(self):
        rec = self.env['approval.level.pr'].search([('level', '=', 1)])
        return rec.id

    def action_approve(self):
        view_id = self.env.ref('atta_purchase_request.crm_remark_wizard_wizard_view').id
        return {'type': 'ir.actions.act_window',
                'name': _('Remarks'),
                'res_model': 'pr.remark.wizard',
                'target': 'new',
                'view_mode': 'form',
                'views': [[view_id, 'form']],
                'context': {'is_process_2': True},
                }

    next_approval_id = fields.Many2one('approval.level.pr', string='Next Approval', tracking=True,
                                       default=_get_next_approval_id, copy=False)
    next_approval_user_ids = fields.Many2many('res.users', string='Next Approval By',
                                              compute='_compute_next_approval_user_id', store=True)
    is_button = fields.Boolean('Is button', compute='_compute_is_button')
    is_last_level = fields.Boolean('Is button', compute='_compute_is_button')
    remark_ids = fields.One2many('remarks.approval.pr', 'purchase_request_id', string='Remarks', tracking=True)
    location_dest_id = fields.Many2one(
        'stock.location', 'Destination Location',
        help="Location where the system will stock the finished products.", compute="_compute_location_dest_id")
    readonly_field = fields.Boolean(string="Readonly", compute="_compute_readonly_field")

    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            if self.search_count([
                ('name', '=', rec.name),
                ('company_id', '=', rec.company_id.id),
            ]) <= 1:
                continue
            field_name_string = self.fields_get(
                ['name'], ['string']
            )['name']['string']
            raise ValidationError(_(
                '%s must be unique.'
            ) % field_name_string)

    def _compute_readonly_field(self):
        for request in self:
            if request.next_approval_id.level == 3:
                request.readonly_field = True
            else:
                request.readonly_field = False

    def _compute_location_dest_id(self):
        for request in self:
            if request.order_ids:
                if request.order_ids.picking_ids:
                    location_dest_ids = request.order_ids.picking_ids.mapped('location_dest_id')
                    if location_dest_ids:
                        request.location_dest_id = location_dest_ids[0]
                    else:
                        request.location_dest_id = False
                else:
                    request.location_dest_id = False
            else:
                request.location_dest_id = False

    @api.depends('line_ids.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.line_ids:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.depends('line_ids.request_deliver_date')
    def compute_min_request_deliver_date(self):
        for rec in self:
            request_deliver_dates = rec.line_ids.filtered(
                'request_deliver_date').mapped('request_deliver_date')
            rec.min_request_deliver_date = request_deliver_dates \
                                           and min(request_deliver_dates)

    @api.depends('line_ids.schedule_date')
    def compute_min_schedule_date(self):
        for rec in self:
            schedule_dates = rec.line_ids.filtered(
                'schedule_date').mapped('schedule_date')
            rec.min_schedule_date = schedule_dates and min(schedule_dates)

    @api.depends('line_ids.po_creation_state')
    def compute_po_creation_state(self):
        for rec in self:
            if not rec.line_ids:
                rec.po_creation_state = 'not'
                continue
            states = rec.line_ids.mapped('po_creation_state')
            if states.count('not'):
                rec.po_creation_state = 'not'
            elif states.count('fully'):
                rec.po_creation_state = 'fully'
            else:
                rec.po_creation_state = 'partially'

    @api.depends('line_ids')
    def compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    @api.depends('line_ids.order_line_ids')
    def compute_order_ids(self):
        for rec in self:
            rec.order_line_ids = rec.line_ids.mapped('order_line_ids')
            rec.order_ids = rec.order_line_ids.mapped('order_id')
            rec.order_count = len(rec.order_ids)

    @api.depends()
    def compute_has_access_right(self):
        has_group_2nd_approval = self.user_has_groups(
            'atta_purchase_request.purchase_request_group_second_approval')
        self.update({'has_access_right': has_group_2nd_approval})

    @api.onchange('min_request_deliver_date')
    def onchange_min_request_deliver_date(self):
        self.request_deliver_date = self.min_request_deliver_date

    @api.onchange('min_schedule_date')
    def onchange_min_schedule_date(self):
        self.schedule_date = self.min_schedule_date

    name = fields.Char(
        string='Request Reference',
        required=True,
        default=DEFAULT_NAME,
        index=True,
        readonly=True,
    )
    state = fields.Selection(
        selection=STATE,
        string='Status',
        required=True,
        default='draft',
        tracking=True,
    )
    create_uid = fields.Many2one(
        comodel_name='res.users',
        string='Requester',
        default=lambda self: self.env.uid,
        readonly=True,
    )
    create_date = fields.Datetime(
        readonly=True,
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department',
        required=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Buyer',
        tracking=True,
    )

    line_ids = fields.One2many(
        comodel_name='purchase.request.line',
        inverse_name='request_id',
        string='Request Lines',
    )
    line_count = fields.Integer(
        string='Request Line Count',
        compute='compute_line_count'
    )

    order_line_ids = fields.Many2many(
        comodel_name='purchase.order.line',
        string='Purchase Order Lines',
        compute='compute_order_ids',
    )

    order_ids = fields.Many2many(
        comodel_name='purchase.order',
        string='Purchase Order',
        compute='compute_order_ids',
    )

    order_count = fields.Integer(
        string='Purchase Order Count',
        compute='compute_order_ids',
    )

    currency_rate_ids = fields.One2many(
        comodel_name='purchase.request.currency.rate',
        inverse_name='request_id',
        string='Currency Rate',
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        index=True,
        default=lambda self: self.env.user.company_id.id,
        domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)],
    )
    currency_id = fields.Many2one(
        related='company_id.currency_id',
        store=True,
    )
    amount_untaxed = fields.Monetary(
        string='Untaxed Amount',
        readonly=True,
        compute='_amount_all',
        store=True,
    )
    amount_tax = fields.Monetary(
        string='Taxes Amount',
        readonly=True,
        compute='_amount_all',
        store=True,
    )
    amount_total = fields.Monetary(
        string='Total Amount',
        readonly=True,
        compute='_amount_all',
        store=True,
    )

    description = fields.Text(
    )
    note = fields.Text(
        string='Notes',
    )

    po_creation_state = fields.Selection(
        selection=PO_CREATION_STATE_SELECTION,
        string='RFQ/PO Creation Status',
        compute='compute_po_creation_state',
        store=True,
    )

    request_deliver_date = fields.Date(
        string='Requested Delivery Date',
        required=True,
    )
    min_request_deliver_date = fields.Date(
        string='Min Requested Delivery Date',
        compute='compute_min_request_deliver_date',
    )

    schedule_date = fields.Datetime(
        string='Scheduled Date',
    )
    min_schedule_date = fields.Datetime(
        string='Min Scheduled Date',
        compute='compute_min_schedule_date',
    )

    submit_date = fields.Datetime(
        string='Submitted Date',
        readonly=True,
    )

    first_approve_uid = fields.Many2one(
        comodel_name='res.users',
        string='1st Approver',
        readonly=True,
    )
    first_approve_date = fields.Datetime(
        string='1st Approved Date',
        readonly=True,
    )
    second_approve_uid = fields.Many2one(
        comodel_name='res.users',
        string='2nd Approver',
        readonly=True,
    )
    second_approve_date = fields.Datetime(
        string='2nd Approved Date',
        readonly=True,
    )
    third_approve_uid = fields.Many2one(
        comodel_name='res.users',
        string='3rd Approver',
        readonly=True,
    )
    third_approve_date = fields.Datetime(
        string='3rd Approved Date',
        readonly=True,
    )
    fourth_approve_uid = fields.Many2one(
        comodel_name='res.users',
        string='4th Approver',
        readonly=True,
    )
    fourth_approve_date = fields.Datetime(
        string='4th Approved Date',
        readonly=True,
    )
    done_uid = fields.Many2one(
        comodel_name='res.users',
        string='Done by',
        readonly=True,
    )
    done_date = fields.Datetime(
        string='Done Date',
        readonly=True,
    )
    cancel_uid = fields.Many2one(
        comodel_name='res.users',
        string='Canceled by',
        readonly=True,
    )
    cancel_date = fields.Datetime(
        string='Canceled Date',
        readonly=True,
    )

    has_access_right = fields.Boolean(
        compute='compute_has_access_right'
    )
    has_access_right = fields.Boolean(
        compute='compute_has_access_right'
    )
    request_type = fields.Selection([('storable', 'Storable'),
                                     ('equipment', 'Equipment'),
                                     ('expense', 'Expense Transfer')],
                                     string='Creation Status')
    allocation_count = fields.Integer(string="Allocation", compute="_compute_allocation_count")
    expense_count = fields.Integer(string="Expense", compute="_compute_expense_count")
    is_show_button_type = fields.Boolean(string="Is Show", compute="_compute_is_show_button_type")
    show_rfq_button = fields.Boolean(string="Is Show Rfq Button", compute="_compute_show_button")
    show_expense_button = fields.Boolean(string="Show Expense Button", compute="_compute_show_button")
    show_allocation_button = fields.Boolean(string="Show Allocation Button", compute="_compute_show_button")
    is_avlible = fields.Boolean(string="Is Avalible")
    rfq_show = fields.Boolean(string="Is rfq show")

    def action_submit(self):
        for rec in self:
            if rec.create_uid != self.env.user:
                raise UserError(_(
                    'Only %s can submit this purchase request!'
                ) % rec.create_uid.name)
            if not rec.line_ids:
                raise UserError(_(
                    'Request lines must not be empty!'
                ))
        self.write({
            'state': 'first',
            'submit_date': fields.Datetime.now(),
        })
        self.line_ids.filtered('product_id').write({'is_edited': False})

    def _compute_is_show_button_type(self):
        for request in self:
            if request.next_approval_id.is_last_approval:
                request.is_show_button_type = True
                if request.is_avlible:
                    request.rfq_show = False
                else:
                    request.rfq_show = True
            else:
                request.is_show_button_type = False
                request.rfq_show = True

    def _compute_show_button(self):
        for request in self:
            if any(line.rfq_create for line in request.line_ids):
                request.show_rfq_button = True
            else:
                request.show_rfq_button = False
            if any(line.allocation_create for line in request.line_ids):
                request.show_allocation_button = True
            else:
                request.show_allocation_button = False
            if any(line.expense_create for line in request.line_ids):
                request.show_expense_button = True
            else:
                request.show_expense_button = False


    def _compute_expense_count(self):
        for request in self:
            request.expense_count = self.env['stock.picking'].search_count([('purchase_request_id', '=', request.id)])

    def _compute_allocation_count(self):
        for request in self:
            request.allocation_count = self.env['allcation.request'].search_count([('purchase_request_id', '=', request.id)])

    def action_first_approve(self):
        self.write({
            'state': 'second',
            'first_approve_date': fields.Datetime.now(),
            'first_approve_uid': self.env.uid,
        })

    def action_create_rfq(self):
        return {
            'name': _('Create RFQ/PO'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.request.line.create.purchase.order.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'is_create_view': True,
                'model_data_id': self.id,
            },
        }

    def action_create_allocation(self):
        line_ids = self.line_ids.filtered(lambda x: not x.is_allocation)
        if not line_ids:
            raise ValidationError(_("All Ready Allocation are created!."))

        purchase_not_done = self.order_ids.filtered(lambda x: x.state not in ['cancel', 'done', 'purchase'])
        if purchase_not_done:
            raise ValidationError("Please Confirm Purchase Order")
        if self.order_ids.picking_ids:
            picking_ids = self.order_ids.picking_ids
            if all([picking.state != 'done' for picking in picking_ids.filtered(lambda x: x.state != 'cancel')]):
                raise ValidationError("Please Complete The Receipt")

        return {
            'name': _('Create Allcation'),
            'type': 'ir.actions.act_window',
            'res_model': 'allcation.request.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    def action_create_expense(self):

        purchase_not_done = self.order_ids.filtered(lambda x: x.state not in ['cancel', 'done', 'purchase'])
        if purchase_not_done:
            raise ValidationError("Please Confirm Purchase Order")
        if self.order_ids.picking_ids:
            picking_ids = self.order_ids.picking_ids
            if all([picking.state != 'done' for picking in picking_ids.filtered(lambda x: x.state != 'cancel')]):
                raise ValidationError("Please Complete The Receipt")

        return {
            'name': _('Create Expense Transfer'),
            'type': 'ir.actions.act_window',
            'res_model': 'expense.transfer.wizard.data',
            'view_mode': 'form',
            'target': 'new',
        }

    def action_second_approve(self):
        params = self.env['ir.config_parameter'].sudo()
        is_required_vendor_in_pr = params.get_param(
            'atta_purchase_request.is_required_vendor_in_pr',
        )
        for rec in self:
            if not rec.user_id:
                rec.user_id = self.env.user
            for line in rec.line_ids:
                if not line.product_id and line.quantity > 0:
                    raise UserError(_(
                        'Please enter products for all request lines!'
                    ))
                if is_required_vendor_in_pr and not line.partner_id:
                    raise UserError(_(
                        'Please enter vendors for all request lines!'
                    ))
                if line.quantity > 0 and not line.schedule_date:
                    raise UserError(_(
                        'Please enter scheduled date for all request lines!'
                    ))
        self.write({
            'state': 'third',
            'second_approve_date': fields.Datetime.now(),
            'second_approve_uid': self.env.uid,
        })

    def action_third_approve(self):
        params = self.env['ir.config_parameter'].sudo()
        has_pr_4th_approve = params.get_param(
            'atta_purchase_request.has_pr_4th_approve',
        )
        pr_4th_approve_amount = float(params.get_param(
            'atta_purchase_request.pr_4th_approve_amount',
            default=0,
        ))
        self.write({
            'third_approve_date': fields.Datetime.now(),
            'third_approve_uid': self.env.uid,
        })
        for rec in self:
            need_4th_approval = all([
                has_pr_4th_approve,
                rec.amount_untaxed >= pr_4th_approve_amount,
                not rec._context.get('no_4th_approval'),
            ])
            rec.state = need_4th_approval and 'fourth' or 'final'

    def action_4th_approve(self):
        self.write({
            'state': 'final',
            'fourth_approve_date': fields.Datetime.now(),
            'fourth_approve_uid': self.env.uid,
        })

    def action_done(self):
        orders = self.sudo().mapped('order_line_ids.order_id')
        if orders.filtered(lambda o: o.state not in ['done', 'cancel']):
            raise UserError(_(
                'You cannot complete a purchase request when '
                'the related purchase orders are in process!',
            ))
        self.write({
            'state': 'done',
            'done_date': fields.Datetime.now(),
            'done_uid': self.env.uid,
        })

    def action_unlock(self):
        self.write({
            'state': 'final',
        })

    def action_cancel(self):
        for rec in self:
            if rec.state == 'final' and rec.order_line_ids:
                raise UserError(_(
                    'You cannot cancel a purchase request '
                    'that has been created purchase order. '
                    'Please unlink or delete related purchase orders first!'
                ))
        self.write({
            'state': 'canceled',
            'cancel_date': fields.Datetime.now(),
            'cancel_uid': self.env.uid,
        })

    def action_draft(self):
        self.write({
            'state': 'draft',
            'submit_date': False,
            'first_approve_date': False,
            'first_approve_uid': False,
            'second_approve_date': False,
            'second_approve_uid': False,
            'third_approve_date': False,
            'third_approve_uid': False,
            'fourth_approve_date': False,
            'fourth_approve_uid': False,
            'done_date': False,
            'done_uid': False,
            'cancel_date': False,
            'cancel_uid': False,
        })
        self.line_ids.write({'is_edited': True})

    def action_set_request_deliver_date_to_lines(self):
        self.line_ids.write({
            'request_deliver_date': self.request_deliver_date,
        })

    def action_set_schedule_date_to_lines(self):
        self.line_ids.write({
            'schedule_date': self.schedule_date,
        })

    def action_view_line(self):
        [action] = self.env.ref(
            'atta_purchase_request.purchase_request_line_action').read()
        action.update({
            'domain': [('id', 'in', self.line_ids.ids)],
        })
        return action

    def action_view_order(self):
        [action] = self.env.ref('purchase.purchase_form_action').read()
        action.update({
            'domain': [('id', 'in', self.order_ids.ids)],
        })
        return action

    def action_view_allocation(self):
        orders = self.env['allcation.request'].search([('purchase_request_id', '=', self.id)])
        return {
            'name': _('Allocation Request'),
            'view_mode': 'tree,form',
            'res_model': 'allcation.request',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', orders.ids)],
        }

    def action_view_expense(self):
        orders = self.env['stock.picking'].search([('purchase_request_id', '=', self.id)])
        return {
            'name': _('Expense Transfers'),
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', orders.ids)],
        }

    @api.model
    def default_get(self, fields_list):
        result = super(PurchaseRequest, self).default_get(fields_list)
        currencies = self.env['res.currency'].search([])
        result['currency_rate_ids'] = [
            (0, 0, {
                'currency_id': currency.id,
                'rate': currency.rate,
            }) for currency in currencies
        ]

        employees = self.env.user.employee_ids
        employee = employees and employees[0]
        if employee:
            department = employee.department_id
            result['department_id'] = department.id
        return result

    def copy(self, default={}):
        self.ensure_one()
        default['name'] = self.env['ir.sequence'].next_by_code(
            'purchase_request_rollback')
        return super(PurchaseRequest, self).copy(default)

    @api.model
    def create(self, values):
        if values.get('name', DEFAULT_NAME) == DEFAULT_NAME:
            values['name'] = self.env['ir.sequence'].next_by_code(
                'purchase_request_rollback')
        return super(PurchaseRequest, self).create(values)

    def unlink(self):
        for rec in self:
            if rec.state != 'canceled':
                raise UserError(_(
                    'Please cancel purchase requests before deleting!'
                ))
        return super(PurchaseRequest, self).unlink()
