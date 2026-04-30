# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    
    cancel_done_picking = fields.Boolean(
        string="Cancel Done Delivery?",
        related="company_id.cancel_done_picking",
        readonly=False,
    )

