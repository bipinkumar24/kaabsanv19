# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    state = fields.Selection(selection_add=[('validate', "Validate")])
    is_posted = fields.Boolean(string="Is posted")

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    state = fields.Selection(selection_add=[('validate', "Validate")])
    is_validate = fields.Boolean(string="Is Validate?", copy=False)

    def action_validate_data(self):
        # Odoo 19 no longer exposes stock.valuation.layer. Legacy valuation
        # posting code is kept commented for migration reference.
        # Valuation = self.env['stock.valuation.layer']
        # for production in self:
        #     moves = (production.move_raw_ids | production.move_finished_ids | production.scrap_ids.mapped('move_ids'))
        #     valuation_ids = Valuation.search([('stock_move_id', 'in', moves.ids)])
        #     account_moves = valuation_ids.mapped('account_move_id').filtered(
        #         lambda m: m.state != 'posted'
        #     )
        #     if account_moves:
        #         account_moves._post()
        #     production.is_validate = True
        for production in self:
            production.is_validate = True

    def action_mrp_production_change(self):
        for order in self:
            if order.state == 'draft':
                order.move_raw_ids = [(5, 0, 0)]
                order._onchange_move_raw()

                finished_vals = order._get_moves_finished_values()
                for mv in finished_vals:
                    self.env['stock.move'].sudo().create(mv)

    def action_cancel(self):
        res = super(MrpProduction, self).action_cancel()
        self.write({'is_validate': False})
        return res
