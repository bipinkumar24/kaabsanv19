
# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import datetime
import pytz
from odoo.exceptions import UserError,Warning
from odoo.exceptions import UserError,ValidationError



class Multi_equipment_request(models.Model):
    _name = "multiple.overtime.request"
    _description = "Multiple Overtime Request"
    _inherit = ['mail.thread','mail.activity.mixin']
    
    name = fields.Char(string='Name', required=True, readonly=True, default=lambda self: ('New'))
    employee_ids = fields.Many2many('hr.employee','rel_multiple_employee',string="Employees" ,required=True)
    department_id = fields.Many2one('hr.department',string="Department",required=False)
    department_manager_id = fields.Many2one('hr.employee',string="Manager")
    include_in_payroll = fields.Boolean(string = "Include In Payroll",default=False)
    
    approve_date = fields.Datetime(string="Approve Date",readonly=True)
    approve_by_id = fields.Many2one('res.users',string="Approve By",readonly=True)
    dept_approve_date = fields.Datetime(string="Department Approve Date",readonly=True)
    dept_manager_id = fields.Many2one('res.users',string="Department Manager",readonly=True)
    num_of_hours = fields.Float(string="Number Of Hours")

    notes = fields.Text(string="Notes")

    state = fields.Selection([('new','New'),('first_approve','Waiting For First Approve'),('dept_approve','Waiting For Department Approve'),
                                ('done','Done'),('refuse','Refuse')],string="State",default='new')
    bill_ids = fields.Many2many('account.move', string="Account Move", copy=False)
    overtime_line_ids = fields.One2many('overtime.line.multiple', 'multiple_overtime_id', string='Overtime Lines')

    @api.model
    def create(self, vals):
        if vals.get('name', ('New')) == ('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'multiple.overtime.request') or ('New')
        res = super(Multi_equipment_request, self).create(vals)
        return res

    def _get_overtime_expense_account(self, product):
        accounts = product.product_tmpl_id._get_product_accounts()
        expense_account = product.property_account_expense_id or accounts.get('expense')
        if not expense_account:
            raise ValidationError(
                _('No expense account is configured for overtime product "%s".') % product.display_name
            )
        return expense_account


    def confirm_action(self):

        self.write({'state' : 'first_approve'})
        return

    def first_approve_action(self):
        self.write({'state' : 'dept_approve',
                    'approve_by_id' : self.env.user.id,
                    'approve_date' : fields.Datetime.now()})        
        return

    def dept_approve_action(self):
        if not self.bill_ids:


            list_bills = []
            for rec in self.overtime_line_ids:
                if not rec.employee_id.department_id.product_id:
                    raise ValidationError(_('Please Configure Overtime Product in Employee Department!'))
                product_id = rec.employee_id.department_id.product_id
                expense_account = self._get_overtime_expense_account(product_id)

                partner_id = rec.employee_id.partner_id
                if not partner_id:
                    partner_id = self.env['res.partner'].create({'name': rec.name})
                    rec.employee_id.partner_id = partner_id.id

                hr_contract_id = self.env['hr.contract'].search([('employee_id', '=', rec.employee_id.id), ('state', '=', 'open')])

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
                            'price_unit': (rec.num_of_hours * hr_contract_id.wage) / 240
                        })
                    ],
                })
                bill_id.multiple_overtime_request_id = self.id
                list_bills.append(bill_id.id)
        if list_bills:
            self.write({'bill_ids': [(6, 0, list_bills)]})
        self.write({'state' : 'done',
                    'dept_manager_id' : self.env.user.id,
                    'dept_approve_date' : fields.Datetime.now()})       
        return


    def refuse_action(self):
        self.write({'state' : 'refuse'})
        return

class OvertimeLineMultiple(models.Model):
    _name = "overtime.line.multiple"

    multiple_overtime_id = fields.Many2one('multiple.overtime.request', 'Multiple Overtime Request')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    num_of_hours = fields.Float(string="Number Of Hours")
