from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    asset_id = fields.Many2one('account.asset', string='Asset')
    is_equipment = fields.Boolean(string='Is Equipment')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    asset_id = fields.Many2one(
        'account.asset',
        related='product_tmpl_id.asset_id',
        readonly=False,
        store=False,
    )
