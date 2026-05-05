from odoo import fields, models


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    not_storable = fields.Boolean(
        string="Not Storable",
        default=False,
        help="Check this if the requested items are not stored in inventory (e.g., services, expenses).",
    )
