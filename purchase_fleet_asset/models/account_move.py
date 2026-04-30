# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    linked_to = fields.Reference(
        selection=[
            ('fleet.vehicle', 'Fleet Vehicle'),
            ('account.asset', 'Asset'),
        ],
        string='Fleet / Asset',
        index=True,
        copy=True,
        help="Fleet vehicle or asset this bill line was purchased for.",
    )
