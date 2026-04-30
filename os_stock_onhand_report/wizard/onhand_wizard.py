# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import fields, models


class ExportStockInfoWiz(models.TransientModel):
    _name = "stock.onhand.wiz"
    _description = "Stock Onhand Report Wizard"

    location_ids = fields.Many2many("stock.location", string="Location", domain=[("usage", "=", "internal")])
    category_ids = fields.Many2many("product.category", string="Category")
    product_ids = fields.Many2many("product.product", string="Products")
    date_from = fields.Date(string="Date")
    display_current_stock = fields.Boolean(string="Display Current Stock")

    def print_stock_onhand_report(self):
        return self.env.ref(
            "os_stock_onhand_report.action_stock_onhand_report").report_action(
            self)

    def data_fetch_from_move(self, location, product):
        date_from = "1900-01-01"
        date_to = self.date_from or fields.Date.context_today(self)

        # Ensure location is a tuple inside a list for SQL parameter substitution
        locations_id = ([location.id],)

        query = """
            SELECT
                line.date AS date,
                line.product_id AS product_id,
                line.qty_done AS product_qty,
                line.product_uom_id AS product_uom,
                0.0 AS unit_cost,
                move.reference AS reference,
                move.partner_id AS partner_id,
                move.origin AS origin,
                move.id as stock_move_id,
                line.location_id AS location_id,
                line.location_dest_id AS location_dest_id,
                CASE 
                    WHEN move.location_dest_id = %s AND move.reference LIKE '%%INT%%' THEN line.qty_done 
                    ELSE line.qty_in
                END AS product_in,
                CASE 
                    WHEN move.location_id = %s AND move.reference LIKE '%%INT%%' THEN line.qty_done 
                    ELSE line.qty_out
                END AS product_out,
                move.picking_id AS picking_id
            FROM stock_move_line line
            LEFT JOIN stock_move move ON move.id = line.move_id
            WHERE line.state = 'done'
            AND (move.location_id = ANY(%s) OR move.location_dest_id = ANY(%s))
            AND line.product_id = %s
            AND move.date::DATE BETWEEN %s AND %s
        """

        self._cr.execute(query, (location.id, location.id, locations_id, locations_id, product.id, date_from, date_to))
        result = self._cr.fetchall()

        # Convert to dictionary
        columns = [desc[0] for desc in self._cr.description]
        data = [dict(zip(columns, row)) for row in result]
        fallback_cost = product.standard_price or 0.0
        for row in data:
            if not row.get("unit_cost"):
                row["unit_cost"] = fallback_cost

        return data  # Return list of dictionaries

    def get_onhand_products(self, loc):
        lst = []
        for rec in self:
            domain = [("location_id", "child_of", [loc.id])]
            if rec.category_ids:
                domain.append(("product_id.categ_id", "in",
                               [categ.id for categ in rec.category_ids]))
            if rec.product_ids:
                domain.append(("product_id", "in", rec.product_ids.ids))
            locations = self.env["stock.quant"].search(domain)
            for prod in locations:
                lst.append({
                    'code': prod.product_id.default_code,
                    'product': prod.product_id.name,
                    'qty': round(prod.quantity, 4),
                    'cost': round(prod.product_id.standard_price, 4),
                    'total': round(round(prod.quantity,4) * round(prod.product_id.standard_price,4), 4),
                })
            return lst

    def get_all_data(self):
        data_prepare = []
        product_ids = self.product_ids if self.product_ids else self.env["product.product"].search([("categ_id", "in", self.category_ids.ids)]) if self.category_ids else []

        for product in product_ids:
            data = [product.name]
            total_qty = 0
            price = 0
            data_prepare_prise = []
            last_date = False

            for location in self.location_ids:
                product_balance = 0
                transactions = self.data_fetch_from_move(location, product)
                sorted_transactions = sorted(transactions, key=lambda x: x['date'])
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
                    refrensh = last_transaction.get('reference')
                    stock_move_id = last_transaction.get('stock_move_id')
                    cost = last_transaction.get('unit_cost') or product.standard_price or 0.0
                    transactions_id = self.env["stock.move"].search([("id", "=", stock_move_id)])

                    if transactions_id:
                        # Odoo 19 removed stock.valuation.layer and the legacy
                        # valuation_unit_price field, so use the latest move cost
                        # from the report data with product cost as fallback.
                        data_prepare_prise.append({'date': transactions_id.date, 'price': cost, 'name': transactions_id.reference})
                        last_price = cost
                        if price == 0.0:
                            price = cost
                        elif price and cost and price < cost:
                            price = cost
                total_qty += product_balance
                data.append(round(product_balance, 4))
            # Group data by date (ignoring time)
            grouped_data = defaultdict(list)
            for entry in data_prepare_prise:
                date = entry['date'].date()  # Only keep the date part
                grouped_data[date].append(entry['price'])

            # Process each date to get the correct price (only single value returned)
            final_price = None
            for date, prices in grouped_data.items():
                latest_date = max(grouped_data.keys())
                # Get the prices for the latest date
                prices = grouped_data[latest_date]
                prices.sort(reverse=True)
                # If the highest price is 0, select the second-highest
                if prices[0] == 0 and len(prices) > 1:
                    final_price = prices[1]
                else:
                    final_price = prices[0]

            # Output the final selected price
            price = final_price
            data.append(round(total_qty, 4))
            data.append(round(price, 4) if price else 0)
            data.append(round(round(total_qty, 4) * round(price, 4), 4) if price else 0)

            data_prepare.append(data)

        return data_prepare

    def data_with_location(self, location):
        final_data = []

        if self.product_ids:
            for product in self.product_ids:
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
                        'price': round(round(product_balance,4) * round(price,4), 4) if price else 0
                    })
        if self.category_ids:
            product_ids = self.env["product.product"].search([("categ_id", "in", self.category_ids.ids)])
            for product in product_ids:
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
                        'price': round(round(product_balance,4) * round(price,4), 4) if price else 0
                    })

        return final_data
