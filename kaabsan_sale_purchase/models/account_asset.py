from odoo import fields, models


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    brand_id = fields.Many2one('fleet.vehicle.model.brand', string='Brand')
    is_visible_fleet = fields.Boolean(string='Visible In Fleet')
    is_visible_maintenance = fields.Boolean(string='Visible In Maintenance')
    is_visible_product = fields.Boolean(string='Visible In Product')
