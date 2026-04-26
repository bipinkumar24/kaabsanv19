# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, fields


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    state = fields.Selection(selection_add=[
        ('cancel', 'Cancel')])

    def action_inventory_scrap_cancel(self):
        for rec in self:
            rec.sudo().mapped('move_ids').sudo().write({'state': 'cancel'})
            rec.sudo().mapped('move_ids').mapped(
                'move_line_ids').sudo().write({'state': 'cancel'})
            rec._sh_unreseve_qty()
            rec.sudo().write({'state': 'cancel'})

    def action_inventory_cancel_scrap_draft(self):
        for rec in self:
            rec.sudo().mapped('move_ids').sudo().write({'state': 'draft'})
            rec.sudo().mapped('move_ids').mapped(
                'move_line_ids').sudo().write({'state': 'draft'})
            rec._sh_unreseve_qty()
            rec.sudo().write({'state': 'draft'})
            move_ids = rec.sudo().mapped('move_ids')
            for move in move_ids:
                # for account_move in move.account_move_ids:
                account_move = move.account_move_id
                if account_move.state == 'posted':
                    account_move.button_draft()
                    
            # for move in rec.stock_move_ids:
            #     move.write({'state': 'draft'})
            #     move.mapped('move_line_ids').sudo().write({'state': 'draft'})
            #     move._sh_unreseve_qty()
            #     move.sudo().write({'state': 'draft'})
            #     move_ids = move
            #     for move_data in move_ids:
            #         # for account_move in move_data.account_move_ids:
            #         account_move = move_data.account_move_id
            #         if account_move.state == 'posted':
            #             account_move.button_draft()

    def action_inventory_cancel_scrap_delete(self):
        for rec in self:
            rec.sudo().mapped('move_ids').sudo().write({'state': 'draft'})
            rec.sudo().mapped('move_ids').mapped(
                'move_line_ids').sudo().write({'state': 'draft'})
            rec._sh_unreseve_qty()
            rec.sudo().mapped('move_ids').sudo().unlink()
            rec.sudo().mapped('move_ids').mapped('move_line_ids').sudo().unlink()
            rec.sudo().write({'state': 'draft'})
            rec.sudo().unlink()

    def _sh_unreseve_qty(self):
        for move_line in self.sudo().mapped('move_ids').sudo().mapped('move_line_ids'):
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
        if self.company_id.scrap_operation_type == 'cancel':

            self.sudo().mapped('move_ids').sudo().write({'state': 'cancel'})
            self.sudo().mapped('move_ids').mapped(
                'move_line_ids').sudo().write({'state': 'cancel'})
            self._sh_unreseve_qty()
            self.sudo().write({'state': 'cancel'})

        elif self.company_id.scrap_operation_type == 'cancel_draft':

            self.sudo().mapped('move_ids').sudo().write({'state': 'draft'})
            self.sudo().mapped('move_ids').mapped(
                'move_line_ids').sudo().write({'state': 'draft'})
            self._sh_unreseve_qty()
            self.sudo().write({'state': 'draft'})

        elif self.company_id.scrap_operation_type == 'cancel_delete':

            self.sudo().mapped('move_ids').sudo().write({'state': 'draft'})
            self.sudo().mapped('move_ids').mapped(
                'move_line_ids').sudo().write({'state': 'draft'})
            self._sh_unreseve_qty()
            self.sudo().mapped('move_ids').sudo().unlink()
            self.sudo().mapped('move_ids').mapped('move_line_ids').sudo().unlink()
            self.sudo().write({'state': 'draft'})
            self.sudo().unlink()

            return {
                'name': 'Stock Scrap',
                'type': 'ir.actions.act_window',
                'res_model': 'stock.scrap',
                'view_type': 'form',
                'view_mode': 'list,form',
                'target': 'current',
            }


class Move(models.Model):
    _inherit = 'stock.move'

    def _sh_unreseve_qty(self):
        for move_line in self.sudo().mapped('move_line_ids'):
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

    def action_move_cancel(self):
        for rec in self:

            print("ABDibasid---------------------------1111--------------------------------***************--------------")
            rec.sudo().write({'state': 'cancel'})
            rec.mapped('move_line_ids').sudo().write({'state': 'cancel'})
            rec._sh_unreseve_qty()

    def action_move_cancel_draft(self):
        for rec in self:
            print("ABDibasid-------------------------222----------------------------------***************--------------")
            rec.sudo().write({'state': 'draft'})
            rec.mapped('move_line_ids').sudo().write({'state': 'draft'})
            rec._sh_unreseve_qty()

    def action_move_cancel_delete(self):
        for rec in self:
            print("ABDibasid------------------3333-----------------------------------------***************--------------")
            rec.sudo().write({'state': 'draft'})
            rec.mapped('move_line_ids').sudo().write({'state': 'draft'})
            rec._sh_unreseve_qty()
            rec.mapped('move_line_ids').sudo().unlink()
            rec.sudo().unlink()


class Picking(models.Model):
    _inherit = 'stock.picking'

    # def action_picking_cancel(self):
    #     for rec in self:
    #         if rec.sudo().mapped('move_ids_without_package'):
    #             rec.sudo().mapped('move_ids_without_package').sudo().write(
    #                 {'state': 'cancel'})
    #             rec.sudo().mapped('move_ids_without_package').mapped(
    #                 'move_line_ids').sudo().write({'state': 'cancel'})
    #             rec._sh_unreseve_qty()
    #         rec.sudo().write({'state': 'cancel'})

    # def action_picking_cancel_draft(self):
    #     for rec in self:
    #         if rec.sudo().mapped('move_ids_without_package'):
    #             rec.sudo().mapped('move_ids_without_package').sudo().write(
    #                 {'state': 'draft'})
    #             rec.sudo().mapped('move_ids_without_package').mapped(
    #                 'move_line_ids').sudo().write({'state': 'draft'})
    #             rec._sh_unreseve_qty()
    #         rec.sudo().write({'state': 'draft'})

    # def action_picking_cancel_delete(self):
    #     for rec in self:
    #         if rec.sudo().mapped('move_ids_without_package'):
    #             rec.sudo().mapped('move_ids_without_package').sudo().write(
    #                 {'state': 'draft'})
    #             rec.sudo().mapped('move_ids_without_package').mapped(
    #                 'move_line_ids').sudo().write({'state': 'draft'})
    #             rec._sh_unreseve_qty()
    #             rec.sudo().mapped('move_ids_without_package').mapped(
    #                 'move_line_ids').sudo().unlink()
    #             rec.sudo().mapped('move_ids_without_package').sudo().unlink()
    #         rec.sudo().write({'state': 'draft', 'show_mark_as_todo': True})
    #         rec.sudo().unlink()

    # def _sh_unreseve_qty(self):
    #     for move_line in self.sudo().mapped('move_ids_without_package').mapped('move_line_ids'):
    #         # unreserve qty
    #         quant = self.env['stock.quant'].sudo().search([('location_id', '=', move_line.location_id.id),
    #                                                        ('product_id', '=',
    #                                                         move_line.product_id.id),
    #                                                        ('lot_id', '=', move_line.lot_id.id)], limit=1)

    #         if quant:
    #             quant.write({'quantity': quant.quantity + move_line.qty_done})

    #         quant = self.env['stock.quant'].sudo().search([('location_id', '=', move_line.location_dest_id.id),
    #                                                        ('product_id', '=',
    #                                                         move_line.product_id.id),
    #                                                        ('lot_id', '=', move_line.lot_id.id)], limit=1)

    #         if quant:
    #             quant.write({'quantity': quant.quantity - move_line.qty_done})


    def action_picking_cancel(self):
        for rec in self:
            move_lines = rec.move_line_ids.filtered(lambda ml: not ml.package_id)
            if move_lines:
                # Cancel related stock moves
                move_lines.mapped('move_id').sudo().write({'state': 'cancel'})
                # Cancel the move lines
                move_lines.sudo().write({'state': 'cancel'})
                rec._sh_unreserve_qty(move_lines)
            rec.sudo().write({'state': 'cancel'})

    def action_picking_cancel_draft(self):
        for rec in self:
            move_lines = rec.move_line_ids.filtered(lambda ml: not ml.package_id)
            if move_lines:
                move_lines.mapped('move_id').sudo().write({'state': 'draft'})
                move_lines.sudo().write({'state': 'draft'})
                rec._sh_unreserve_qty(move_lines)
            rec.sudo().write({'state': 'draft'})

    def action_picking_cancel_delete(self):
        for rec in self:
            move_lines = rec.move_line_ids.filtered(lambda ml: not ml.package_id)
            if move_lines:
                move_lines.mapped('move_id').sudo().write({'state': 'draft'})
                move_lines.sudo().write({'state': 'draft'})
                rec._sh_unreserve_qty(move_lines)
                # Delete move lines and moves
                move_lines.sudo().unlink()
                move_lines.mapped('move_id').sudo().unlink()
            rec.sudo().write({'state': 'draft', 'show_mark_as_todo': True})
            rec.sudo().unlink()

    def _sh_unreserve_qty(self, move_lines):
        """Unreserve stock quantities for given move_lines."""
        for move_line in move_lines:
            # Increase qty in source location
            quant = self.env['stock.quant'].sudo().search([
                ('location_id', '=', move_line.location_id.id),
                ('product_id', '=', move_line.product_id.id),
                ('lot_id', '=', move_line.lot_id.id)
            ], limit=1)
            if quant:
                quant.write({'quantity': quant.quantity + move_line.qty_done})

            # Decrease qty in destination location
            quant = self.env['stock.quant'].sudo().search([
                ('location_id', '=', move_line.location_dest_id.id),
                ('product_id', '=', move_line.product_id.id),
                ('lot_id', '=', move_line.lot_id.id)
            ], limit=1)
            if quant:
                quant.write({'quantity': quant.quantity - move_line.qty_done})

    # def sh_cancel(self):

    #     if self.company_id.picking_operation_type == 'cancel':
    #         # if self.sudo().mapped('move_ids_without_package'):
    #         if self.move_line_ids.filtered(lambda ml: not ml.package_id):
    #             self.sudo().mapped('move_ids_without_package').sudo().write(
    #                 {'state': 'cancel'})
    #             self.sudo().mapped('move_ids_without_package').mapped(
    #                 'move_line_ids').sudo().write({'state': 'cancel'})
    #             self._sh_unreseve_qty()
    #         self.sudo().write({'state': 'cancel'})

    #     elif self.company_id.picking_operation_type == 'cancel_draft':
    #         # if self.sudo().mapped('move_ids_without_package'):
    #         if self.move_line_ids.filtered(lambda ml: not ml.package_id):
    #             self.move_line_ids.filtered(lambda ml: not ml.package_id).sudo().write(
    #                 {'state': 'draft'})
    #             self.sudo().mapped('move_line_ids').filtered(lambda ml: not ml.package_id).sudo().write({'state': 'draft'})
    #             self._sh_unreseve_qty()
    #         self.sudo().write({'state': 'draft'})

    #     elif self.company_id.picking_operation_type == 'cancel_delete':
    #         if self.sudo().mapped('move_ids_without_package'):
    #             self.sudo().mapped('move_ids_without_package').sudo().write(
    #                 {'state': 'draft'})
    #             self.sudo().mapped('move_ids_without_package').mapped(
    #                 'move_line_ids').sudo().write({'state': 'draft'})
    #             self._sh_unreseve_qty()
    #             self.sudo().mapped('move_ids_without_package').mapped(
    #                 'move_line_ids').sudo().unlink()
    #             self.sudo().mapped('move_ids_without_package').sudo().unlink()
    #         self.sudo().write({'state': 'draft', 'show_mark_as_todo': True})
    #         self.sudo().unlink()

    #         return {
    #             'name': 'Transfers',
    #             'type': 'ir.actions.act_window',
    #             'res_model': 'stock.picking',
    #             'view_type': 'form',
    #             'view_mode': 'list,kanban,form,calendar',
    #             'search_view_id': [self.env.ref('stock.view_picking_internal_search').id],
    #             'target': 'current',
    #         }

    def sh_cancel(self):
        for picking in self:
            move_lines = picking.move_line_ids.filtered(lambda ml: not ml.package_id)
            
            if picking.company_id.picking_operation_type == 'cancel':
                if move_lines:
                    # Cancel related stock moves
                    move_lines.mapped('move_id').sudo().write({'state': 'cancel'})
                    # Cancel the move lines
                    move_lines.sudo().write({'state': 'cancel'})
                    picking._sh_unreserve_qty(move_lines)
                picking.sudo().write({'state': 'cancel'})

            elif picking.company_id.picking_operation_type == 'cancel_draft':
                if move_lines:
                    # Reset related stock moves to draft
                    move_lines.mapped('move_id').sudo().write({'state': 'draft'})
                    # Reset move lines to draft
                    move_lines.sudo().write({'state': 'draft'})
                    picking._sh_unreserve_qty(move_lines)
                picking.sudo().write({'state': 'draft'})

            elif picking.company_id.picking_operation_type == 'cancel_delete':
                if move_lines:
                    # Reset moves and move lines to draft
                    move_lines.mapped('move_id').sudo().write({'state': 'draft'})
                    move_lines.sudo().write({'state': 'draft'})
                    picking._sh_unreserve_qty(move_lines)
                    # Delete move lines and moves
                    move_lines.sudo().unlink()
                    move_lines.mapped('move_id').sudo().unlink()
                picking.sudo().write({'state': 'draft', 'show_mark_as_todo': True})
                picking.sudo().unlink()

        # Return to Transfers view
        return {
            'name': 'Transfers',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_type': 'form',
            'view_mode': 'list,kanban,form,calendar',
            'search_view_id': self.env.ref('stock.view_picking_internal_search').id,
            'target': 'current',
        }
