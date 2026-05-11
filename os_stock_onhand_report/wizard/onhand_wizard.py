# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError
from collections import defaultdict


class ExportStockInfoWiz(models.TransientModel):
    _name = 'stock.onhand.wiz'
    _description = 'Stock Onhand Report Wizard'

    location_ids = fields.Many2many('stock.location', string="Location", domain=[('usage', '=', 'internal')])
    category_ids = fields.Many2many('product.category', string="Category")
    product_ids = fields.Many2many('product.product', string="Products")
    date_from = fields.Date(string="Date")
    display_current_stock = fields.Boolean(string="Display Current Stock")

    def print_stock_onhand_report(self):
        if not self.product_ids and not self.category_ids:
            raise UserError(_("Please select Products or a Product Category before printing."))
        # If no locations selected, default to all internal locations
        if not self.location_ids:
            self.location_ids = self.env['stock.location'].search([('usage', '=', 'internal')])
        return self.env.ref('os_stock_onhand_report.action_stock_onhand_report').report_action(self)

    def data_fetch_from_move(self, location, product):
        date_from = "1900-01-01"
        date_to = self.date_from or fields.Date.context_today(self)

        locations_id = [location.id]

        query = """
            SELECT
                line.date           AS date,
                line.product_id     AS product_id,
                line.quantity       AS product_qty,
                line.product_uom_id AS product_uom,
                -- prefer our computed valuation price; fall back to price_unit for historical/migrated moves
                COALESCE(NULLIF(move.valuation_unit_price, 0), move.price_unit, 0) AS unit_cost,
                move.reference      AS reference,
                move.partner_id     AS partner_id,
                move.origin         AS origin,
                move.id             AS stock_move_id,
                line.location_id    AS location_id,
                line.location_dest_id AS location_dest_id,
                CASE
                    WHEN move.location_dest_id = %s THEN line.quantity
                    ELSE 0
                END AS product_in,
                CASE
                    WHEN move.location_id = %s THEN line.quantity
                    ELSE 0
                END AS product_out,
                move.picking_id     AS picking_id
            FROM stock_move_line line
            LEFT JOIN stock_move move ON move.id = line.move_id
            WHERE line.state = 'done'
              AND (move.location_id = ANY(%s) OR move.location_dest_id = ANY(%s))
              AND line.product_id = %s
              AND move.date::DATE BETWEEN %s AND %s
        """

        self._cr.execute(
            query,
            (location.id, location.id, locations_id, locations_id, product.id, date_from, date_to),
        )
        columns = [desc[0] for desc in self._cr.description]
        return [dict(zip(columns, row)) for row in self._cr.fetchall()]

    def get_onhand_products(self, loc):
        lst = []
        for rec in self:
            domain = [('location_id', 'child_of', [loc.id])]
            if rec.category_ids:
                domain.append(('product_id.categ_id', 'in', rec.category_ids.ids))
            if rec.product_ids:
                domain.append(('product_id', 'in', rec.product_ids.ids))
            for quant in self.env['stock.quant'].search(domain):
                lst.append({
                    'code': quant.product_id.default_code,
                    'product': quant.product_id.name,
                    'qty': round(quant.quantity, 4),
                    'cost': round(quant.product_id.standard_price, 4),
                    'total': round(round(quant.quantity, 4) * round(quant.product_id.standard_price, 4), 4),
                })
            return lst

    def get_all_data(self):
        data_prepare = []
        if self.product_ids:
            product_ids = self.product_ids
        elif self.category_ids:
            product_ids = self.env['product.product'].search([('categ_id', 'in', self.category_ids.ids)])
        else:
            product_ids = self.env['product.product']

        for product in product_ids:
            data = [product.name]
            total_qty = 0
            price = 0
            data_prepare_price = []

            for location in self.location_ids:
                product_balance = 0
                transactions = self.data_fetch_from_move(location, product)
                sorted_transactions = sorted(transactions, key=lambda x: x['date'])

                # Carry forward the last known unit cost to fill None gaps
                last_unit_cost = None
                for record in sorted_transactions:
                    if record['unit_cost'] is not None:
                        last_unit_cost = record['unit_cost']
                    else:
                        record['unit_cost'] = last_unit_cost

                last_transaction = sorted_transactions[-1] if sorted_transactions else None
                for line in sorted_transactions:
                    product_balance += line.get('product_in', 0) - line.get('product_out', 0)

                if last_transaction:
                    cost = last_transaction.get('unit_cost')
                    stock_move_id = last_transaction.get('stock_move_id')
                    move = self.env['stock.move'].browse(stock_move_id)

                    if move.exists():
                        # Use valuation_unit_price from the move; fall back to last non-zero
                        # sql cost if the move's price is zero. Never write back to the
                        # computed field — use a local variable instead.
                        unit_price = move.valuation_unit_price
                        if unit_price == 0.0:
                            for record in reversed(sorted_transactions):
                                if record.get('unit_cost', 0) != 0.0:
                                    unit_price = record['unit_cost']
                                    break

                        data_prepare_price.append({
                            'date': move.date,
                            'price': unit_price,
                            'name': move.reference,
                        })
                        if price == 0.0:
                            price = cost
                        elif price and cost and price < cost:
                            price = cost

                total_qty += product_balance
                data.append(round(product_balance, 4))

            # Pick the highest price on the latest date
            grouped_data = defaultdict(list)
            for entry in data_prepare_price:
                grouped_data[entry['date'].date()].append(entry['price'])

            final_price = None
            if grouped_data:
                latest_date = max(grouped_data.keys())
                prices = sorted(grouped_data[latest_date], reverse=True)
                if prices[0] == 0 and len(prices) > 1:
                    final_price = prices[1]
                else:
                    final_price = prices[0]

            price = final_price
            data.append(round(total_qty, 4))
            data.append(round(price, 4) if price else 0)
            data.append(round(round(total_qty, 4) * round(price, 4), 4) if price else 0)
            data_prepare.append(data)

        return data_prepare

    def data_with_location(self, location):
        final_data = []

        product_list = list(self.product_ids)
        if self.category_ids:
            product_list += list(self.env['product.product'].search([('categ_id', 'in', self.category_ids.ids)]))

        for product in product_list:
            product_balance = 0
            price = 0
            transactions = self.data_fetch_from_move(location, product)

            for line in transactions:
                product_balance += line.get('product_in', 0) - line.get('product_out', 0)
                price = line.get('unit_cost', 0)

            if product_balance > 0:
                final_data.append({
                    'product_name': product.name,
                    'balance': round(product_balance, 4),
                    'cost_price': round(price, 4) if price else 0,
                    'price': round(round(product_balance, 4) * round(price, 4), 4) if price else 0,
                })

        return final_data
