# models/leave_report_wizard.py
from odoo import models, fields, api

class LeaveReportWizard(models.TransientModel):
    _name = 'leave.report.wizard'
    _description = 'Leave Report Wizard'

    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)
    employee_ids = fields.Many2many('hr.employee', string='Employees')

    def print_report(self):
        self.ensure_one()
        data = {
            'form': self.read()[0],
        }
        return self.env.ref('employee_leave_report.action_leave_report').report_action(self, data=data)

class LeaveReport(models.AbstractModel):
    _name = 'report.employee_leave_report.leave_report_template'
    _description = 'Leave Report'

    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        employee_ids = data['form'].get('employee_ids', [])

        domain = [
            ('request_date_from', '>=', date_start),
            ('request_date_to', '<=', date_end),
            ('state', 'in', ['validate', 'validate1']),
        ]

        if employee_ids:
            domain += [('employee_id', 'in', employee_ids)]

        # Fetch leave records
        leaves = self.env['hr.leave'].search(domain, order='employee_id, request_date_from')

        # Group leaves by employee
        grouped_leaves = {}
        for leave in leaves:
            grouped_leaves.setdefault(leave.employee_id, []).append(leave)

        return {
            'doc_ids': docids,
            'doc_model': 'leave.report.wizard',
            'docs': grouped_leaves,
            'data': data,
        }
