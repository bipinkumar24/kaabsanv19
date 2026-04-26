from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PurchaseRequestCurrencyRate(models.Model):
    _name = 'purchase.request.currency.rate'
    _rec_name = 'currency_id'
    _description = 'Purchase Request Currency Rate'

    @api.constrains('rate')
    def _check_rate(self):
        for rec in self:
            if rec.rate < 0:
                raise ValidationError(_(
                    'Currency Rate must be greater than 0!'
                ))

    request_id = fields.Many2one(
        comodel_name='purchase.request',
        string='Request',
        required=True,
        index=True,
        ondelete='cascade',
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
        readonly=True,
    )
    rate = fields.Float(
        required=True,
        digits='Payment Terms',
    )

