from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AppraisalRating(models.Model):
    _name = 'hr.odoo.appraisal.rating'
    _description = 'Odoo Appraisal Rating'

    name = fields.Char(string="Rating Name", required=True)
    range_from = fields.Integer(string="Range From", required=True)
    range_to = fields.Integer(string="Range To", required=True)

    @api.constrains('range_from', 'range_to')
    def _check_range_values(self):
        for rec in self:
            if rec.range_from >= rec.range_to:
                raise ValidationError("'Range From' must be less than 'Range To'")
