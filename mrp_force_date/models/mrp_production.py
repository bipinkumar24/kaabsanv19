# -*- coding: utf-8 -*-

from odoo import fields, models


class Production(models.Model):
    _inherit = "mrp.production"

    force_inventory_date = fields.Datetime(string="Force Inventory Date")
