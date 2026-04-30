# -*- coding: utf-8 -*-

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        moves_todo = super()._action_done(cancel_backorder)
        for mv in moves_todo:
            if mv.production_id and mv.production_id.force_inventory_date:
                mv.write({
                    "date": mv.production_id.force_inventory_date,
                })
                mv.move_line_ids.write({
                    "date": mv.production_id.force_inventory_date,
                })
            elif mv.raw_material_production_id and mv.raw_material_production_id.force_inventory_date:
                mv.write({
                    "date": mv.raw_material_production_id.force_inventory_date,
                })
                mv.move_line_ids.write({
                    "date": mv.raw_material_production_id.force_inventory_date,
                })
        return moves_todo
