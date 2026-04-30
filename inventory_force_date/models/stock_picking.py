# -*- coding: utf-8 -*-

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    force_inventory_date = fields.Datetime(string="Force Inventory Date")
