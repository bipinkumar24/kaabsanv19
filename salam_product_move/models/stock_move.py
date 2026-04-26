# -*- coding: utf-8 -*-

from odoo import api, fields, models
class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.depends('quantity', 'picking_id','state','production_id')
    def _compute_stock_in_and_out(self):
        for line in self:
            if line.production_id:
                line.qty_in = 0.00
                line.qty_out = line.quantity
                line.qty_total = line.quantity * -1
            elif not line.picking_id.picking_type_id:
                if line.location_dest_id.usage == 'inventory':
                    line.qty_in = 0.00
                    line.qty_out = line.quantity
                    line.qty_total = line.quantity * -1
                else:
                    line.qty_in = line.quantity
                    line.qty_out = 0.00
                    line.qty_total = line.quantity
            elif line.picking_id.picking_type_id.code == 'incoming':
                line.qty_in = line.quantity
                line.qty_out = 0.00
                line.qty_total = line.quantity
            elif line.picking_id.picking_type_id.code == 'outgoing':
                line.qty_in = 0.00
                line.qty_out = line.quantity
                line.qty_total = line.quantity * -1
            elif line.picking_id.picking_type_id.code == 'internal':
                if line.location_id.usage == 'internal' and line.location_dest_id.usage == 'internal':
                    line.qty_in = 0.00
                    line.qty_out = 0.00
                    line.qty_total = 0.00
                elif line.location_id.usage == 'internal':
                    line.qty_in = 0.00
                    line.qty_out = line.quantity
                    line.qty_total = line.quantity * -1
                elif line.location_dest_id.usage == 'internal':
                    line.qty_in = line.quantity
                    line.qty_out = 0.00
                    line.qty_total = line.quantity
            else:
                line.qty_in = 0.00
                line.qty_out = 0.00
                line.qty_total = 0.00

    @api.depends('quantity', 'picking_id', 'product_id', 'state')
    def _compute_balance(self):
        for line in self:
            if line.state == 'done':
                previous_line_rec = self.env['stock.move.line'].search([
                    ('id', '<', line.id),
                    ('product_id', '=', line.product_id.id),
                    ('state', '=', 'done')
                ], limit=1, order='id desc')
                
                if not previous_line_rec:
                    line.balance_qty = line.qty_total
                else:
                    line.balance_qty = previous_line_rec.balance_qty + line.qty_total
            else:
                line.balance_qty = 0.00

    def update_move_qty_line(self):
        move_line_ids = self.env['stock.move.line'].search([])
        for line in move_line_ids:
            line._compute_stock_in_and_out()
            line._compute_balance()

    def action_compaute_in_out_sent(self):
        for line in self:
            line._compute_stock_in_and_out()
            line._compute_balance()

    qty_in = fields.Float(string='Stock In', compute='_compute_stock_in_and_out', store=True)
    qty_out = fields.Float(string='Stock Out', compute='_compute_stock_in_and_out', store=True)
    qty_total = fields.Float(string='Balance Qty', compute='_compute_stock_in_and_out', store=True)
    balance_qty = fields.Float(string='History Qty', compute='_compute_balance', store=True)
