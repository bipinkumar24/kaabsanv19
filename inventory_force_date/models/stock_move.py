# -*- coding: utf-8 -*-

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    force_inventory_date = fields.Datetime(string="Force Inventory Date")

    def _action_done(self, cancel_backorder=False):
        moves_todo = super()._action_done(cancel_backorder)
        for mv in moves_todo:
            if mv.force_inventory_date:
                mv.write({
                    "date": mv.force_inventory_date,
                })
                mv.move_line_ids.write({
                    "date": mv.force_inventory_date,
                })
            elif mv.picking_id and mv.picking_id.force_inventory_date:
                mv.write({
                    "date": mv.picking_id.force_inventory_date,
                })
                mv.move_line_ids.write({
                    "date": mv.picking_id.force_inventory_date,
                })
        return moves_todo
