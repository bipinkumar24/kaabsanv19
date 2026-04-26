from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class mylot(models.Model):
    # Odoo 19 migration: hr.contract/hr_contract no longer exists in core.
    # Old inheritance kept for migration reference:
    # _inherit = "hr.contract"
    _inherit = "hr.version"

    thesalary = fields.Monetary(string='Salary', required=True, tracking=True, help="Employee's monthly salary.")
