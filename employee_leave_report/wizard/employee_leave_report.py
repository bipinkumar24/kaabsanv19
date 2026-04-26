from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.tools.translate import _

class HrEmployeeLeave(models.TransientModel):

    _name = 'hr.employee.leave'
    _description = 'Employee leave Report'

    holiday_type = fields.Selection([
        ('Approved', 'On Going'),
        ('PrePlanned', 'PrePlanned'),
    ], string='Select Status', required=True, default='Approved')



    def print_report(self):
        self.ensure_one()
        [data] = self.read()
        data['emp'] = self.env.context.get('active_ids', [])
        employees = self.env['hr.employee'].search([])
        datas = {
            'ids': [],
            'model': 'hr.employee',
            'form': data,
        }
        return self.env.ref('employee_leave_report.action_employee_leave_report_new').report_action(employees, data=datas)


class HrEmployeeLeaveReport(models.AbstractModel):
    _name = 'report.employee_leave_report.report_hr_employee_temp'
    _description = 'Holidays Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data or 'form' not in data:
            raise UserError(_("Form content is missing, this report cannot be printed."))

        h_type = data['form'].get('holiday_type', '')
        today = fields.Date.context_today(self)

        # remaining_leave is a non-stored display field, so use stored request dates in domains.
        leaves = self.env['hr.leave'].search([('request_date_to', '>=', today)])
        
        # Filter confirmed leaves and other leaves
        confirmed_leaves = leaves.filtered(lambda e: e.state == 'validate')
        other_leaves = leaves.filtered(lambda e: e.state != 'validate')

        # Get leave IDs for confirmed leaves
        leave_ids = [
            leave.id for leave in confirmed_leaves
            if leave.request_date_from and leave.request_date_from <= today <= leave.request_date_to
        ]
        
        # Get IDs for other leaves
        other_leave_ids = [
            leave.id for leave in other_leaves
            if leave.request_date_from and leave.request_date_from >= today
        ]

        # Determine the leaves to return based on conditions
        if h_type == 'Approved' and leave_ids:
            emp_leaves = self.env['hr.leave'].browse(leave_ids)
        elif other_leave_ids:
            emp_leaves = self.env['hr.leave'].browse(other_leave_ids)
        else:
            emp_leaves = self.env['hr.leave'] 

        return {
            'doc_ids': docids,
            'doc_model': 'hr.leave',
            'docs': emp_leaves,
            'holiday_type': h_type,
        }
