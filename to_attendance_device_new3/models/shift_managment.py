from odoo import models, fields, api

from odoo.exceptions import ValidationError

class AttendanceActivity(models.Model):
    _name = 'ti.shift.management'

    name = fields.Char(string="Name", required=True)
    mm_from = fields.Integer(string="Minutes From")
    mm_to = fields.Integer(string="Minutes To")
    hh_from = fields.Integer(string="Hours From")
    hh_to = fields.Integer(string="Hours To")
    number = fields.Integer(string="Shift Numbering")
    code = fields.Char(string="Code")

    employees = fields.Many2many('hr.employee',string="Employees")

    @api.constrains('hh_from', 'hh_to','number')
    def check_hh(self):
        for rec in self:
            print(rec.hh_from)
            if rec.hh_from < 1:
                raise ValidationError('Hours From should be greater then 0')
            if rec.hh_to < 1:
                raise ValidationError('Hours To should be greater then 0')
            if rec.number < 1:
                raise ValidationError('Shift Numbering should be greater then 0')

    @api.constrains('employees')
    def check_employee(self):
        for rec in self:
            if rec.code == 'Third':
                # Get all shift records excluding 'Third' and their employees
                other_all_shift_ids = self.env['ti.shift.management'].search([('code', '!=', 'Third')])
                other_employee_ids = other_all_shift_ids.mapped('employees').ids
                
                # Check if there is an intersection between rec.employees and other_employee_ids
                common_employees = set(rec.employees.ids) & set(other_employee_ids)
                
                if common_employees:
                    # Get the names of the employees in the intersection
                    common_employee_names = self.env['hr.employee'].browse(common_employees).mapped('name')
                    
                    # Raise a validation error with employee names in the message
                    raise ValidationError("The following employees are assigned to another shift: %s" % ', '.join(common_employee_names))
            if rec.code in ['First', 'Second']:
                # Get all shift records excluding 'Third' and their employees
                other_all_shift_ids = self.env['ti.shift.management'].search([('code', '=', 'Third')])
                other_employee_ids = other_all_shift_ids.mapped('employees').ids
                
                # Check if there is an intersection between rec.employees and other_employee_ids
                common_employees = set(rec.employees.ids) & set(other_employee_ids)
                
                if common_employees:
                    # Get the names of the employees in the intersection
                    common_employee_names = self.env['hr.employee'].browse(common_employees).mapped('name')
                    
                    # Raise a validation error with employee names in the message
                    raise ValidationError("The following employees are assigned to another shift: %s" % ', '.join(common_employee_names))
