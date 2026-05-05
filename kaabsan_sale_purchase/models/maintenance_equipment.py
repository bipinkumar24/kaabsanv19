from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    asset_id = fields.Many2one('account.asset', string='Asset')
    product_tmpl_id = fields.Many2one('product.template', string='Product Template')
