# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Inventory(models.Model):
    _inherit = "stock.quant"

    force_inventory_date = fields.Datetime(string="Force Inventory Date")

    def _get_inventory_move_values(self, qty, location_id, location_dest_id, out=False):
        res = super()._get_inventory_move_values(qty, location_id, location_dest_id, out)
        if self.force_inventory_date and self.env.user.has_group("inventory_force_date.group_force_inventory_date"):
            res.update({
                "force_inventory_date": self.force_inventory_date,
            })
        return res

    def action_apply_inventory(self):
        res = super().action_apply_inventory()
        self.force_inventory_date = False
        return res

    @api.model
    def _get_inventory_fields_write(self):
        inventory_fields = super()._get_inventory_fields_write()
        inventory_fields.append("force_inventory_date")
        return inventory_fields

    def action_set_inventory_quantity_to_zero(self):
        res = super().action_set_inventory_quantity_to_zero()
        self.action_reset_force_inventory_date()
        return res

    def action_reset_force_inventory_date(self):
        self.force_inventory_date = False
