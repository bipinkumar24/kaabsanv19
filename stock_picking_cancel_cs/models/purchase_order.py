from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    cancel_done_picking = fields.Boolean(string="Cancel Done Delivery?", compute="_compute_cancel_done_picking")

    @api.depends("picking_ids.state")
    def _compute_cancel_done_picking(self):
        for order in self:
            can_cancel = False
            if self.env.user.has_group("stock_picking_cancel_cs.group_cancel_delivery_order"):
                for picking in order.picking_ids:
                    if picking.state != "cancel":
                        can_cancel = True
                        break
            order.cancel_done_picking = can_cancel

    def cancel_picking(self):
        if len(self.picking_ids) == 1:
            self.picking_ids.with_context({"Flag": True}).action_cancel()
            return self.action_view_delivery()
        else:
            return self.action_cancel_selected_picking()
        
    def action_view_delivery(self):
        action = self.env.ref("stock.action_picking_tree_all").read()[0]
        picking_records = self.mapped('picking_ids')
        if picking_records:
            action["views"] = [(self.env.ref("stock.view_picking_form").id, "form")]
            action["res_id"] = picking_records.id
        return action

    def action_cancel_selected_picking(self):
        pickings = []
        for picking in self.picking_ids:
            if picking.state != "cancel":
                pickings.append(picking.id)
        return {
            "type": "ir.actions.act_window",
            "res_model": "cancel.picking.wizard",
            "view_mode": "form",
            "views": [(self.env.ref("stock_picking_cancel_cs.delivery_cancel_form_cft").id, "form")],
            "target": "new",
            "context": {
                    "pickings": pickings,
            },
        }
