# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import datetime
import pytz
from odoo.exceptions import UserError,ValidationError

PAYMENT_STATE_SELECTION = [
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
        ('invoicing_legacy', 'Invoicing App Legacy'),
]


class my_equipment_request(models.Model):
    _name = "overtime.request"
    _rec_name = "employee_id"
    _description = "Overtime Request"
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(string='Name', required=True, readonly=True, default=lambda self: ('New'))
    employee_id = fields.Many2one('hr.employee',string="Employee" ,required=True)
    department_id = fields.Many2one('hr.department',string="Department")
    department_manager_id = fields.Many2one('hr.employee',string="Manager")
    include_in_payroll = fields.Boolean(string = "Include In Payroll")
    
    approve_date = fields.Datetime(string="Approve Date",readonly=True)
    approve_by_id = fields.Many2one('res.users',string="Approve By",readonly=True)

    dept_approve_date = fields.Datetime(string="Department Approve Date",readonly=True)
    dept_manager_id = fields.Many2one('res.users',string="Department Manager",readonly=True)

    num_of_hours = fields.Float(string="Number Of Hours" )

    notes = fields.Text(string="Notes")

    state = fields.Selection([('new','New'),('first_approve','Waiting For First Approve'),('dept_approve','Waiting For Department Approve'),
                                ('done','Done'),('refuse','Refuse')],string="State",default='new')
    bill_id = fields.Many2one('account.move', string="Account Move", copy=False)
    payment_state = fields.Selection(PAYMENT_STATE_SELECTION, string="Payment Status", store=True,
                                     readonly=True, copy=False, tracking=True, compute='_compute_payment_state')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'overtime.request') or 'New'
        return super(my_equipment_request, self).create(vals_list)

    @api.depends('bill_id', 'bill_id.payment_state')
    def _compute_payment_state(self):
        for rec in self:
            rec.payment_state = rec.bill_id.payment_state

    def _get_overtime_expense_account(self, product):
        accounts = product.product_tmpl_id._get_product_accounts()
        expense_account = product.property_account_expense_id or accounts.get('expense')
        if not expense_account:
            raise ValidationError(
                _('No expense account is configured for overtime product "%s".') % product.display_name
            )
        return expense_account


    @api.onchange('employee_id')
    def onchange_employee(self):

        self.department_id = self.employee_id.department_id.id
        self.department_manager_id = self.employee_id.department_id.manager_id.id

    def confirm_action(self):
        self.write({'state' : 'first_approve'})
        return

    def first_approve_action(self):
        self.write({'state' : 'dept_approve',
                    'approve_by_id' : self.env.user.id,
                    'approve_date' : fields.Datetime.now()})        
        return

    def dept_approve_action(self):
        if not self.bill_id:
            # product_id = self.env['product.product'].search(
            #     [('default_code', '=', 'overtime'), ('detailed_type', '=', 'service')])
            # if not product_id:
            #     product_id = self.env['product.product'].create({'name': 'Overtime',
            #                                                      'default_code': 'Overtime',
            #                                                      'detailed_type': 'service',
            #                                                      'list_price': 0,
            #                                                      'taxes_id': False
            #                                                      })
            if not self.employee_id.department_id.product_id:
                raise ValidationError(_('Please Configure Overtime Product in Employee Department!'))
            product_id = self.employee_id.department_id.product_id
            expense_account = self._get_overtime_expense_account(product_id)

            partner_id = self.employee_id.partner_id
            if not partner_id:
                partner_id = self.env['res.partner'].create({'name': self.employee_id.name})
                self.employee_id.partner_id = partner_id.id

            hr_contract_id = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'open')])

            level_id = self.env['approval.level.account'].search([('is_finance_approval', '=', True)])
            if not level_id:
                raise ValidationError(_('Please Configure Finance Approval Level!'))

            bill_id = self.env['account.move'].create({
                'move_type': 'in_invoice',
                'partner_id': partner_id.id,
                'date': fields.Datetime.now(),
                'invoice_date': fields.Datetime.now(),
                'is_expense': True,
                'is_overtime': True,
                'next_approval_id': level_id.id,
                'invoice_line_ids': [
                    (0, 0, {
                        'product_id': product_id.id,
                        'account_id': expense_account.id,
                        'name': product_id.name,
                        'quantity': 1,
                        'price_unit': (self.num_of_hours * hr_contract_id.wage) / 240
                    })
                ],
            })
            self.write({'bill_id': bill_id.id})
        self.write({'state' : 'done',
                    'dept_manager_id' : self.env.user.id,
                    'dept_approve_date' : fields.Datetime.now()})       
        return

    def refuse_action(self):
        self.write({'state' : 'refuse'})
        return


