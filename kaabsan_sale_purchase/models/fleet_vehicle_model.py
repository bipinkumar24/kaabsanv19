from odoo import fields, models


class FleetVehicleModel(models.Model):
    _inherit = 'fleet.vehicle.model'

    asset_id = fields.Many2one('account.asset', string='Asset')
