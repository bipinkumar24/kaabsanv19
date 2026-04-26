# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models


class POSOrder(models.Model):
    _inherit = 'pos.order'

    def action_pos_cancel_draft(self):
        for rec in self:
            if rec.company_id.pos_cancel_delivery:
                if rec.sudo().mapped('picking_id'):
                    if rec.sudo().mapped('picking_id').sudo().mapped('move_ids_without_package'):
                        rec.sudo().mapped('picking_id').sudo().mapped(
                            'move_ids_without_package').sudo().write({'state': 'cancel'})
                        rec.sudo().mapped('picking_id').sudo().mapped('move_ids_without_package').mapped(
                            'move_line_ids').sudo().write({'state': 'cancel'})
                    rec._sh_unreseve_qty()
                    rec.sudo().mapped('picking_id').sudo().write(
                        {'state': 'draft', 'show_mark_as_todo': True})

            if rec.company_id.pos_cancel_invoice:

                if rec.mapped('account_move'):
                    if rec.mapped('account_move'):
                        move = rec.mapped('account_move')
                        move_line_ids = move.sudo().mapped('line_ids')

                        reconcile_ids = []
                        if move_line_ids:
                            reconcile_ids = move_line_ids.sudo().mapped('id')

                        reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                            ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                        if reconcile_lines:
                            reconcile_lines.sudo().unlink()

                        move.mapped(
                            'line_ids.analytic_line_ids').sudo().unlink()
                        move_line_ids.sudo().write({'parent_state': 'draft'})
                        move.sudo().write({'state': 'draft'})

                    rec.mapped('account_move').sudo().write({'state': 'draft'})

            if rec.mapped('payment_ids'):
                payment_ids = rec.mapped('payment_ids')
                payment_ids.sudo().unlink()
            rec.sudo().write({'state': 'draft'})

    def action_pos_cancel_delete(self):
        for rec in self:
            if rec.company_id.pos_cancel_delivery:

                if rec.sudo().mapped('picking_id'):
                    if rec.sudo().mapped('picking_id').sudo().mapped('move_ids_without_package'):
                        rec.sudo().mapped('picking_id').sudo().mapped(
                            'move_ids_without_package').sudo().write({'state': 'draft'})
                        rec.sudo().mapped('picking_id').sudo().mapped('move_ids_without_package').mapped(
                            'move_line_ids').sudo().write({'state': 'draft'})
                        rec._sh_unreseve_qty()
                        rec.sudo().mapped('picking_id').sudo().mapped(
                            'move_ids_without_package').sudo().unlink()
                        rec.sudo().mapped('picking_id').sudo().mapped(
                            'move_ids_without_package').mapped('move_line_ids').sudo().unlink()

                    rec.sudo().mapped('picking_id').sudo().write(
                        {'state': 'draft'})
                    rec.sudo().mapped('picking_id').sudo().unlink()

            if rec.company_id.pos_cancel_invoice:

                if rec.mapped('account_move'):
                    if rec.mapped('account_move'):
                        move = rec.mapped('account_move')
                        move_line_ids = move.sudo().mapped('line_ids')

                        reconcile_ids = []
                        if move_line_ids:
                            reconcile_ids = move_line_ids.sudo().mapped('id')

                        reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                            ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                        if reconcile_lines:
                            reconcile_lines.sudo().unlink()

                        move.mapped(
                            'line_ids.analytic_line_ids').sudo().unlink()
                        move_line_ids.sudo().write({'parent_state': 'draft'})
                        move.sudo().write({'state': 'draft'})

                    rec.mapped('account_move').sudo().write(
                        {'state': 'draft', 'name': '/'})
                    rec.mapped('account_move').sudo().with_context(
                        {'force_delete': True}).unlink()

            if rec.mapped('payment_ids'):
                payment_ids = rec.mapped('payment_ids')
                payment_ids.sudo().unlink()

            rec.sudo().write({'state': 'cancel'})
        for rec in self:
            rec.sudo().unlink()

    def _sh_unreseve_qty(self):
        for move_line in self.sudo().mapped('picking_id').mapped('move_ids_without_package').mapped('move_line_ids'):
            # unreserve qty
            quant = self.env['stock.quant'].sudo().search([('location_id', '=', move_line.location_id.id),
                                                           ('product_id', '=',
                                                            move_line.product_id.id),
                                                           ('lot_id', '=', move_line.lot_id.id)], limit=1)

            if quant:
                quant.write({'quantity': quant.quantity + move_line.qty_done})

            quant = self.env['stock.quant'].sudo().search([('location_id', '=', move_line.location_dest_id.id),
                                                           ('product_id', '=',
                                                            move_line.product_id.id),
                                                           ('lot_id', '=', move_line.lot_id.id)], limit=1)

            if quant:
                quant.write({'quantity': quant.quantity - move_line.qty_done})

    def sh_cancel(self):

        if self.company_id.pos_cancel_delivery:
            if self.company_id.pos_operation_type == 'cancel_draft':
                if self.sudo().mapped('picking_id'):
                    if self.sudo().mapped('picking_id').sudo().mapped('move_ids_without_package'):
                        self.sudo().mapped('picking_id').sudo().mapped(
                            'move_ids_without_package').sudo().write({'state': 'cancel'})
                        self.sudo().mapped('picking_id').sudo().mapped('move_ids_without_package').mapped(
                            'move_line_ids').sudo().write({'state': 'cancel'})
                    self._sh_unreseve_qty()
                    self.sudo().mapped('picking_id').sudo().write(
                        {'state': 'draft', 'show_mark_as_todo': True})

            elif self.company_id.pos_operation_type == 'cancel_delete':
                if self.sudo().mapped('picking_id'):
                    if self.sudo().mapped('picking_id').sudo().mapped('move_ids_without_package'):
                        self.sudo().mapped('picking_id').sudo().mapped(
                            'move_ids_without_package').sudo().write({'state': 'draft'})
                        self.sudo().mapped('picking_id').sudo().mapped('move_ids_without_package').mapped(
                            'move_line_ids').sudo().write({'state': 'draft'})
                        self._sh_unreseve_qty()
                        self.sudo().mapped('picking_id').sudo().mapped(
                            'move_ids_without_package').sudo().unlink()
                        self.sudo().mapped('picking_id').sudo().mapped(
                            'move_ids_without_package').mapped('move_line_ids').sudo().unlink()

                    self.sudo().mapped('picking_id').sudo().write(
                        {'state': 'draft'})
                    self.sudo().mapped('picking_id').sudo().unlink()

        if self.company_id.pos_cancel_invoice:

            if self.mapped('account_move'):
                if self.mapped('account_move'):
                    move = self.mapped('account_move')
                    move_line_ids = move.sudo().mapped('line_ids')

                    reconcile_ids = []
                    if move_line_ids:
                        reconcile_ids = move_line_ids.sudo().mapped('id')

                    reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    if reconcile_lines:
                        reconcile_lines.sudo().unlink()

                    move.mapped('line_ids.analytic_line_ids').sudo().unlink()
                    move_line_ids.sudo().write({'parent_state': 'draft'})
                    move.sudo().write({'state': 'draft'})

                if self.company_id.pos_operation_type == 'cancel_draft':
                    self.mapped('account_move').sudo().write(
                        {'state': 'draft'})
                elif self.company_id.pos_operation_type == 'cancel_delete':
                    self.mapped('account_move').sudo().write(
                        {'state': 'draft', 'name': '/'})
                    self.mapped('account_move').sudo().with_context(
                        {'force_delete': True}).unlink()

        if self.mapped('payment_ids'):
            payment_ids = self.mapped('payment_ids')
            payment_ids.sudo().unlink()

        if self.company_id.pos_operation_type == 'cancel_draft':
            self.sudo().write({'state': 'draft'})
        elif self.company_id.pos_operation_type == 'cancel_delete':
            self.sudo().write({'state': 'cancel'})
            self.sudo().unlink()
            return {
                'name': 'POS Order',
                'type': 'ir.actions.act_window',
                'res_model': 'pos.order',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current',
            }
