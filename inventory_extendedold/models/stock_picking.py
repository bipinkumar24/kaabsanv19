# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'


    def button_validate(self):
        for line in self.move_line_ids:
            stock_quant_id = self.env['stock.quant'].search([('product_id','=',line.product_id.id),('location_id','=',line.location_id.id)],limit=1)
            qty_available = stock_quant_id.available_quantity
            if line.product_id.is_storable and  qty_available < line.quantity:
                raise ValidationError(_("%s's Location/Warehouse Has Product With Available QTY %s "%(line.product_id.display_name,qty_available)))
        return super(StockPicking, self).button_validate()
