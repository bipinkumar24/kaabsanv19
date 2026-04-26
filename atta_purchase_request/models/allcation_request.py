from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AllcationRequest(models.Model):
    _inherit = 'allcation.request'

    purchase_request_id = fields.Many2one('purchase.request', string="Purchase Request")
