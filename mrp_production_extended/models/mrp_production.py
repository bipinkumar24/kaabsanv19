# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    state = fields.Selection(selection_add=[('validate', "Validate")])
    is_posted = fields.Boolean(string="Is posted")

    # def action_validate_data(self):
    #     scraps = self.env['stock.scrap'].search([('picking_id', '=', self.id)])
    #     domain = [('id', 'in', (self.move_ids + scraps.move_ids).stock_valuation_layer_ids.ids)]
    #     valuation_ids = self.env['stock.valuation.layer'].search(domain)
    #     for valuation in valuation_ids:
    #         if valuation.account_move_id:
    #             if valuation.account_move_id.state != 'posted':
    #                 valuation.account_move_id._post()
    #     self.sudo().write({'state': 'validate', 'is_posted': True})
    def action_validate_data(self):
        scraps = self.env['stock.scrap'].search([('picking_id', '=', self.id)])
        all_moves = self.move_ids + scraps.move_ids

        # Collect account moves from all possible relations in Odoo 19
        account_move_ids = set()

        for move in all_moves:
            move_fields = move._fields.keys()
            for field_name in ('account_move_ids', 'account_move_id', 'valuation_layer_ids'):
                if field_name in move_fields:
                    related = getattr(move, field_name)
                    if hasattr(related, 'account_move_id'):
                        for layer in related:
                            if layer.account_move_id:
                                account_move_ids.add(layer.account_move_id.id)
                    elif related._name == 'account.move':
                        for am in related:
                            account_move_ids.add(am.id)

        if account_move_ids:
            account_moves = self.env['account.move'].browse(list(account_move_ids))
            for am in account_moves:
                if am.state != 'posted':
                    am._post()

        self.sudo().write({'state': 'validate', 'is_posted': True})


    # def action_unpost_entery(self):
    #     scraps = self.env['stock.scrap'].search([('picking_id', '=', self.id)])
    #     domain = [('id', 'in', (self.move_ids + scraps.move_id).stock_valuation_layer_ids.ids)]
    #     valuation_ids = self.env['stock.valuation.layer'].search(domain)
    #     for valuation in valuation_ids:
    #         if valuation.account_move_id:
    #             if valuation.account_move_id.state == 'posted':
    #                 valuation.account_move_id.button_draft()
    #     self.sudo().write({'state': 'done', 'is_posted': False})
    def action_unpost_entery(self):
        for picking in self:
            scraps = self.env['stock.scrap'].search([('picking_id', '=', picking.id)])
            all_moves = picking.move_ids | scraps.move_ids

            account_move_ids = set()

            for move in all_moves:
                move_fields = move._fields.keys()
                for field_name in ('account_move_ids', 'account_move_id', 'valuation_layer_ids'):
                    if field_name in move_fields:
                        related = getattr(move, field_name)
                        if hasattr(related, 'account_move_id'):
                            for layer in related:
                                if layer.account_move_id:
                                    account_move_ids.add(layer.account_move_id.id)
                        elif hasattr(related, '_name') and related._name == 'account.move':
                            for am in related:
                                account_move_ids.add(am.id)

            if account_move_ids:
                account_moves = self.env['account.move'].browse(list(account_move_ids))
                posted = account_moves.filtered(lambda am: am.state == 'posted')
                if posted:
                    posted.button_draft()

            picking.sudo().write({
                'state': 'done',
                'is_posted': False
            })


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

    # def action_validate_data(self):
    #     domain = [('id', 'in', (self.move_raw_ids + self.move_finished_ids + self.scrap_ids.move_id).stock_valuation_layer_ids.ids)]
    #     valuation_ids = self.env['stock.valuation.layer'].search(domain)
    #     for valuation in valuation_ids:
    #         if valuation.account_move_id:
    #             if valuation.account_move_id.state != 'posted':
    #                 valuation.account_move_id._post()
    #     self.write({'is_validate': True})
        # self.sudo().write({'state': 'validate'})
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
