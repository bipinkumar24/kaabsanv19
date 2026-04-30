# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, exceptions, api, _
from datetime import datetime
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit= 'sale.order'
    
    def action_confirm_inherit(self):
        context = dict(self._context or {})
        data_obj = self.env['ir.model.data']
        view_id=self.env.ref('bi_sale_confirmation_force_date.confirmation_date_wizard')
        # return {
        #     'name': "Select Confirmation Force Date",
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'confirmation.date.wizard',
        #     'view_id': False,
        #     'context': context,
        #     'views': [(view_id.id, 'form')],
        #     'type': 'ir.actions.act_window',
        #     'target': 'new',
        #     'nodestroy': True,
        # }
        return {'type': 'ir.actions.act_window',
                'name': _('Select Confirmation Force Date'),
                'res_model': 'confirmation.date.wizard',
                'target': 'new',
                'view_id': self.env.ref('bi_sale_confirmation_force_date.confirmation_date_wizard').id,
                'view_mode': 'form',
                'context': context
                }
        

class ConfirmDateWizard(models.TransientModel):
    _name = 'confirmation.date.wizard'
    _description = 'Confirmation Date Wizard'

    confirmation_force_date = fields.Datetime(string='Confirm Force Date', index=True, help="Date on which the sales order is confirmed.", copy=False)
   
    def action_confirm(self):
        context = dict(self._context) or {}
        if context.get('active_id', False):
            sale_obj = self.env['sale.order'].browse(context.get('active_id'))
            sale_obj.action_confirm()
            if self.confirmation_force_date:
                sale_obj.date_order = self.confirmation_force_date
            picking = self.env['stock.picking'].search([('sale_id', '=', sale_obj.id), ('state', 'not in', ['cancel'])])
            if not sale_obj.commitment_date:
                for pic in picking:
                    if self.confirmation_force_date:
                        picking.scheduled_date = self.confirmation_force_date
        elif context.get('active_ids', False):
            sale_obj = self.env['sale.order'].browse(context.get('active_ids'))
            for sale in sale_obj:
                sale.action_confirm()
                if self.confirmation_force_date:
                    sale.date_order = self.confirmation_force_date
                picking = self.env['stock.picking'].search([('sale_id', '=', sale.id), ('state', 'not in', ['cancel'])])
                if not sale.commitment_date:
                    for pic in picking:
                        if self.confirmation_force_date:
                            picking.scheduled_date = self.confirmation_force_date

        return True
