# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    activity_ids = fields.One2many(
        'mail.activity', 'res_id', 'Activities',
        auto_join=True,
        groups="base.group_user")

    total_bom_cost = fields.Float("total cost")

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    state = fields.Selection(selection_add=[('validate', "Validate")])
    is_posted = fields.Boolean(string="Is Posted?", copy=False)

    def action_validate_data(self):
        for picking in self:
            scraps = self.env['stock.scrap'].search([('picking_id', '=', picking.id)])
            # Odoo 19 migration: move_lines/stock_valuation_layer_ids no longer drive valuation posting.
            # Old lookup kept for migration reference:
            # domain = [('id', 'in', (picking.move_lines + scraps.move_id).stock_valuation_layer_ids.ids)]
            # valuation_ids = self.env['stock.valuation.layer'].search(domain)
            moves = picking.move_ids | scraps.move_id
            account_moves = moves.mapped('account_move_id')
            account_moves.filtered(lambda move: move.state != 'posted')._post()
            picking.sudo().write({'state': 'validate', 'is_posted': True})

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    state = fields.Selection(selection_add=[('validate', "Validate")])

    is_validate = fields.Boolean(string="Is Validate?", copy=False)

    # @api.depends(
    #     'move_raw_ids.state', 'move_raw_ids.quantity_done', 'move_finished_ids.state',
    #     'workorder_ids.state', 'product_qty', 'qty_producing', 'is_validate')
    # def _compute_state(self):
    #     super()._compute_state()
    #     for production in self:
    #         if production.is_validate and production.state == 'done':
    #             production.state = 'validate'

    def action_validate_data(self):
        for production in self:
            # Odoo 19 migration: stock.valuation.layer is no longer the live posting hook.
            # Old lookup kept for migration reference:
            # domain = [('id', 'in', (production.move_raw_ids + production.move_finished_ids + production.scrap_ids.move_id).stock_valuation_layer_ids.ids)]
            # valuation_ids = self.env['stock.valuation.layer'].search(domain)
            moves = production.move_raw_ids | production.move_finished_ids | production.scrap_ids.move_id
            account_moves = moves.mapped('account_move_id')
            account_moves.filtered(lambda move: move.state != 'posted')._post()
            production.write({'is_validate': True})
            # production.sudo().write({'state': 'validate'})

    def action_cancel(self):
        res = super(MrpProduction, self).action_cancel()
        self.write({'is_validate': False})
        return res
