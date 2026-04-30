from odoo import api, models, fields

class Aasets(models.Model):
    _inherit = 'account.asset'

    asset_tag = fields.Many2many('asset.tag', string='Asset tag')


class Assettag(models.Model):
    _name = 'asset.tag'
    _description = 'interested Areas'

    name = fields.Char(string='Name')
    color = fields.Integer(string='color')

    # Odoo 15 legacy:
    # _sql_constraints = [
    #     ('unique_name', 'unique(name)', _('This Asset tag  already exists !'))
    # ]
    _unique_name = models.Constraint(
        'unique(name)',
        'This Asset tag  already exists !',
    )
