# -*- coding: utf-8 -*-

from odoo import api, models, fields, _

class ProductProduct(models.Model):
    _inherit = "product.product"

    def action_move_qty(self):
        # Find all quants for Cement in WH1/Stock
        quants = self.env['stock.quant'].search([
            ('product_id', '=', self.id),
            ('location_id.complete_name', '=', 'WH1/Stock')
        ])
        for quant in quants:
            # Check if this quant has any stock.move.line history
            moves = self.env['stock.move.line'].search([
                ('product_id', '=', quant.product_id.id),
                ('company_id', '=', quant.company_id.id),
                '|',
                    ('location_id', '=', quant.location_id.id),
                    ('location_dest_id', '=', quant.location_id.id),
            ], limit=1)

            if not moves:
                print(f"Deleting quant ID {quant.id} | Qty: {quant.quantity}")
                query = """DELETE FROM stock_quant WHERE id = %s"""
                params = (quant.id,)
                self._cr.execute(query, params)
            else:
                print(f"Skipping quant ID {quant.id} - has history")
        picking_ids = self.env['stock.picking.type'].search([('code', '=', 'internal')])
        main_quant_ids = self.env['stock.quant'].search([('product_id', '=', self.id),  ('location_id.usage', '=', 'internal')])
        quant_ids = main_quant_ids.filtered(lambda x:not x.owner_id)
        remove_notused_id =  main_quant_ids.filtered(lambda x:x.owner_id)
        for quant in remove_notused_id:
            query = """DELETE FROM stock_quant WHERE id = %s"""
            params = (quant.id,)
            self._cr.execute(query, params)
        move_line_ids = self.env['stock.move.line'].search([('product_id', '=', self.id),('state','=', 'done')])
        total_qty = 0
        for quant in quant_ids:
            total_all_qty = 0
            location_ids = move_line_ids.filtered(lambda x:x.location_id.id == quant.location_id.id or x.location_dest_id.id == quant.location_id.id)
            location_ids = location_ids.sorted(lambda x: x.date)
            for line in location_ids:
                if 'INT' in line.reference:
                    if line.location_id.id == quant.location_id.id:
                        total_all_qty -= line.qty_done
                        total_qty -= line.qty_done
                    elif line.location_dest_id.id == quant.location_id.id:
                        total_all_qty += line.qty_done
                        total_qty += line.qty_done
                    else:
                        total_all_qty += line.qty_total
                        total_qty += line.qty_total
                else:
                    total_all_qty += line.qty_total
                    total_qty += line.qty_total
            qty_update = round(total_all_qty, 2)
            query = """UPDATE stock_quant SET quantity = %s WHERE id = %s"""
            params = (qty_update, quant.id)
            self._cr.execute(query, params)
        internal_location_in_ids = move_line_ids.filtered(lambda x:x.location_id.usage == 'internal').mapped('location_id').ids
        internal_location_out_ids = move_line_ids.filtered(lambda x:x.location_dest_id.usage == 'internal').mapped('location_dest_id').ids
        total_location_data = []
        total_location_data.extend(internal_location_in_ids)
        total_location_data.extend(internal_location_out_ids)
        remove_duplicate = list(set(total_location_data))
        not_set_location = []
        for location in remove_duplicate:
            if location not in quant_ids.mapped('location_id').ids:
                not_set_location.append(location)
        for quant in not_set_location:
            total_all_qty = 0
            in_date = None
            location_ids = move_line_ids.filtered(lambda x:x.location_id.id == quant or x.location_dest_id.id == quant)
            for line in location_ids:
                if line.location_id.usage == 'internal' and line.location_dest_id.usage == 'internal':
                    print("lllllllllllllll22222")
                else:
                    total_all_qty += line.qty_total
                    total_qty += line.qty_total
                    in_date = line.date
            if in_date == None or in_date == False:
                in_date = fields.Datetime.now()
            qty_create = round(total_all_qty, 2)
            query = """INSERT INTO stock_quant (quantity, location_id, product_id, reserved_quantity, in_date)
                   VALUES (%s, %s, %s, %s, %s)"""
            params = (qty_create, quant, self.id, 0, in_date)
            self.env.cr.execute(query, params)
