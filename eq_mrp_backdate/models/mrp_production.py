# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import models, fields, api

 
class Stock_Move(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        res = super(Stock_Move, self)._action_done(cancel_backorder)
        move_fields = self.env['stock.move']._fields.keys()
        for each_move in res:
            production_id = False
            if each_move.production_id:
                production_id = each_move.production_id
            if each_move.raw_material_production_id:
                production_id = each_move.raw_material_production_id
            if production_id and production_id.backdated:
                backdated = production_id.backdated or fields.Datetime.now()
                note = production_id.remark or production_id.name
                each_move.write(
                    {'date': backdated,'date_deadline': backdated,'origin': note})
                each_move.move_line_ids.write(
                    {'date':backdated,'origin':note})
                # Odoo 19 no longer exposes stock valuation layers.
                # if 'stock_valuation_layer_ids' in move_fields:
                #     for valuation_layer in each_move.stock_valuation_layer_ids:
                #         self.env.cr.execute("update stock_valuation_layer set create_date = %s where id = %s", (backdated, valuation_layer.id))
                if 'account_move_ids' in move_fields:
                    for account_move in each_move.account_move_ids:
                        account_move.write({'date':backdated.date()})
        return res


class mrp_production(models.Model):
    _inherit = 'mrp.production'

    backdated = fields.Datetime(string="Backdate", copy=False)
    remark = fields.Char(string="Remark", copy=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
