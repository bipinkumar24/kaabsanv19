from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.constrains('supplier_rank', 'vendor_lead_time')
    def _check_vendor_lead_time(self):
        for rec in self:
            if rec.supplier_rank and not rec.vendor_lead_time >= 0:
                raise ValidationError(_('Lead Time must be greater than 0!'))

    vendor_lead_time = fields.Integer(
        string='Lead Time (Days)',
    )
