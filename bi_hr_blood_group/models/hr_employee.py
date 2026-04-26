from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    blood_group = fields.Selection(
        [
            ("a_positive", "A+"),
            ("a_negative", "A-"),
            ("b_positive", "B+"),
            ("b_negative", "B-"),
            ("ab_positive", "AB+"),
            ("ab_negative", "AB-"),
            ("o_positive", "O+"),
            ("o_negative", "O-"),
        ],
        string="Blood Group",
        groups="hr.group_hr_user",
    )
    age = fields.Integer(
        string="Age",
        compute="_compute_age",
        store=True,
        groups="hr.group_hr_user",
    )

    @api.depends("birthday")
    def _compute_age(self):
        for employee in self:
            if employee.birthday:
                today = fields.Date.context_today(employee)
                employee.age = today.year - employee.birthday.year - (
                    (today.month, today.day) < (employee.birthday.month, employee.birthday.day)
                )
            else:
                employee.age = 0
