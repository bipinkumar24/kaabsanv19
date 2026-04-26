# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models


class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    def action_landed_cost_cancel(self):
        for rec in self:
            if rec.sudo().mapped('account_move_id'):
                move = rec.sudo().mapped('account_move_id')
                move_line_ids = move.sudo().mapped('line_ids')
                reconcile_ids = []
                if move_line_ids:
                    reconcile_ids = move_line_ids.sudo().mapped('id')
                reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                    ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                if reconcile_lines:
                    reconcile_lines.sudo().unlink()
                move.mapped('line_ids.analytic_line_ids').sudo().unlink()
                move.sudo().write({'state': 'draft', 'name': '/'})
                move.sudo().with_context({'force_delete': True}).unlink()

            if rec.mapped('valuation_adjustment_lines'):
                rec.mapped('valuation_adjustment_lines').sudo().unlink()

            if rec.mapped('stock_valuation_layer_ids'):
                rec.mapped('stock_valuation_layer_ids').sudo().unlink()

            rec.sudo().write({'state': 'cancel'})

    def action_landed_cost_cancel_draft(self):
        for rec in self:
            if rec.sudo().mapped('account_move_id'):
                move = rec.sudo().mapped('account_move_id')
                move_line_ids = move.sudo().mapped('line_ids')
                reconcile_ids = []
                if move_line_ids:
                    reconcile_ids = move_line_ids.sudo().mapped('id')
                reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                    ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                if reconcile_lines:
                    reconcile_lines.sudo().unlink()
                move.mapped('line_ids.analytic_line_ids').sudo().unlink()
                move.sudo().write({'state': 'draft', 'name': '/'})
                move.sudo().with_context({'force_delete': True}).unlink()

            if rec.mapped('valuation_adjustment_lines'):
                rec.mapped('valuation_adjustment_lines').sudo().unlink()

            if rec.mapped('stock_valuation_layer_ids'):
                rec.mapped('stock_valuation_layer_ids').sudo().unlink()

            rec.sudo().write({'state': 'draft'})

    def action_landed_cost_cancel_delete(self):
        for rec in self:
            if rec.sudo().mapped('account_move_id'):
                move = rec.sudo().mapped('account_move_id')
                move_line_ids = move.sudo().mapped('line_ids')
                reconcile_ids = []
                if move_line_ids:
                    reconcile_ids = move_line_ids.sudo().mapped('id')
                reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                    ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                if reconcile_lines:
                    reconcile_lines.sudo().unlink()
                move.mapped('line_ids.analytic_line_ids').sudo().unlink()
                move.sudo().write({'state': 'draft', 'name': '/'})
                move.sudo().with_context({'force_delete': True}).unlink()

            if rec.mapped('valuation_adjustment_lines'):
                rec.mapped('valuation_adjustment_lines').sudo().unlink()

            if rec.mapped('stock_valuation_layer_ids'):
                rec.mapped('stock_valuation_layer_ids').sudo().unlink()

            rec.sudo().write({'state': 'cancel'})

        for rec in self:
            rec.sudo().unlink()

    def sh_cancel(self):

        if self.sudo().mapped('account_move_id'):

            move = self.sudo().mapped('account_move_id')
            move_line_ids = move.sudo().mapped('line_ids')
            reconcile_ids = []
            if move_line_ids:
                reconcile_ids = move_line_ids.sudo().mapped('id')
            reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
            if reconcile_lines:
                reconcile_lines.sudo().unlink()

            move.mapped('line_ids.analytic_line_ids').sudo().unlink()
            move.sudo().write({'state': 'draft', 'name': '/'})
            move.sudo().with_context({'force_delete': True}).unlink()

        if self.mapped('valuation_adjustment_lines'):
            self.mapped('valuation_adjustment_lines').sudo().unlink()

        if self.mapped('stock_valuation_layer_ids'):
            self.mapped('stock_valuation_layer_ids').sudo().unlink()

        if self.company_id.landed_cost_operation_type == 'cancel':
            self.sudo().write({'state': 'cancel'})
        elif self.company_id.landed_cost_operation_type == 'cancel_draft':
            self.sudo().write({'state': 'draft'})
        elif self.company_id.landed_cost_operation_type == 'cancel_delete':
            self.sudo().write({'state': 'cancel'})
            self.sudo().unlink()

            return {
                'name': 'Landed Costs',
                'type': 'ir.actions.act_window',
                'res_model': 'stock.landed.cost',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current',
            }
