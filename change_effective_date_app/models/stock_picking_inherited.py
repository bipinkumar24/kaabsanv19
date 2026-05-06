# -*- coding: utf-8 -*-


from odoo import fields, models, api, _
from odoo.exceptions import UserError


class StockPickingInherited(models.Model):
    _inherit = "stock.picking"

    def action_change_effective_date(self):
        xml_id = 'change_effective_date_app.change_effective_date_views_form'
        form_view_id = self.env.ref(xml_id).id
        return {
            'name': _('Change Effective Date'),
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(form_view_id, 'form')],
            'res_model': 'change.effective.date.wizard',
            'type': 'ir.actions.act_window',
            'context': {'default_picking_id': self.id},
            'target': 'new',
        }