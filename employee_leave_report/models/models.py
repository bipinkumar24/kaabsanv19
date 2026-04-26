# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Employee(models.Model):
    _inherit = "hr.employee"

    leave_id = fields.Many2one('hr.leave', compute='_compute_leave_id', string="Current Time Off")

    def _compute_leave_id(self):
        self.leave_id = False  
        holidays = self.env['hr.leave'].sudo().search([('employee_id', 'in', self.ids)]) 
        for holiday in holidays:
            employee = self.filtered(lambda e: e.id == holiday.employee_id.id)
            employee.leave_id = holiday.id 


class HRLeave(models.Model):
    _inherit = 'hr.leave'

    remaining_leave = fields.Integer("Remaining Days", compute='_compute_remaining_leave', store=False)

    @api.depends('date_to', 'request_date_to')
    def _compute_remaining_leave(self):
        for record in self:
            today = fields.Date.context_today(record)
            end_date = record.request_date_to or (record.date_to and record.date_to.date())
            if end_date and today < end_date:
                remaining_days = (end_date - today).days
                record.remaining_leave = max(remaining_days, 0)
            else:
                record.remaining_leave = 0
