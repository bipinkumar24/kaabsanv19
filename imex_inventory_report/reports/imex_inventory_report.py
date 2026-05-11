from odoo import api, fields, models, tools
from odoo.tools.safe_eval import safe_eval

# stock.valuation.layer was removed in Odoo 19.
# Unit cost is now sourced directly from stock.move (price_unit / value/quantity).
_UNIT_COST = (
    "COALESCE(NULLIF(move.price_unit, 0),"
    " CASE WHEN move.quantity != 0 THEN ABS(move.value / move.quantity) ELSE 0 END,"
    " 0)"
)


def _ids(t):
    """Return a SQL-safe (x,y,z) string from a tuple of integer IDs."""
    return "({})".format(",".join(str(int(i)) for i in t)) if t else "(-1)"


def _date(d):
    """Return a SQL-quoted date string."""
    return "'{}'".format(str(d))


class ImexInventoryReport(models.Model):
    _name = "imex.inventory.report"
    _description = "Imex Inventory Report"
    _auto = False

    product_id = fields.Many2one(comodel_name="product.product", readonly=True)
    product_uom = fields.Many2one(comodel_name="uom.uom", readonly=True)
    product_category = fields.Many2one(comodel_name="product.category", readonly=True)
    location = fields.Many2one(comodel_name="stock.location", readonly=True)
    initial = fields.Float(readonly=True)
    initial_amount = fields.Float(readonly=True)
    product_in = fields.Float(readonly=True)
    product_in_amount = fields.Float(readonly=True)
    product_out = fields.Float(readonly=True)
    product_out_amount = fields.Float(readonly=True)
    balance = fields.Float(readonly=True)
    amount = fields.Float(readonly=True)

    def _get_locations(self, location_id, is_groupby_location):
        count_internal_transfer = True
        if location_id:
            if is_groupby_location:
                locations = tuple(self.env["stock.location"].search(
                    [("id", "child_of", location_id.ids)]).ids)
            else:
                locations = tuple(location_id.ids)
        else:
            locations = tuple(self.env["stock.location"].search(
                [("usage", "=", "internal")]).ids)
            if not locations:
                locations = (-1,)
            if not is_groupby_location:
                count_internal_transfer = False
        return locations, count_internal_transfer

    def _get_product_category_ids(self, product_category_ids):
        if product_category_ids:
            product_category_ids = tuple(self.env['product.category'].search(
                [('id', 'child_of', product_category_ids.ids)]).ids)
        else:
            product_category_ids = tuple(self.env["product.category"].search([]).ids)
            if not product_category_ids:
                product_category_ids = (-1,)
        return product_category_ids

    def _get_product_ids(self, product_ids, product_category_ids):
        if product_ids:
            product_ids = tuple(product_ids.ids)
        elif product_category_ids:
            product_ids = tuple(self.env['product.product'].search(
                [('categ_id', 'child_of', product_category_ids.ids)]).ids)
            if not product_ids:
                product_ids = (-1,)
        else:
            product_ids = tuple(self.env["product.product"].search(
                [("active", "=", True)]).ids)
            if not product_ids:
                product_ids = (-1,)
        return product_ids

    def _get_internal_picking_type(self, is_groupby_location):
        internal_picking_type = None
        if not is_groupby_location:
            internal_picking_type = tuple(
                self.env["stock.picking.type"].search([("code", "=", "internal")]).ids)
            if not internal_picking_type:
                internal_picking_type = (-1,)
        return internal_picking_type

    def init_results(self, filter_fields):
        date_from = filter_fields.date_from or "1900-01-01"
        date_to = filter_fields.date_to or fields.Date.context_today(self)
        is_groupby_location = filter_fields.is_groupby_location

        locations, count_internal_transfer = self._get_locations(
            filter_fields.location_id, is_groupby_location)
        product_category_ids = self._get_product_category_ids(
            filter_fields.product_category_ids)
        product_ids = self._get_product_ids(
            filter_fields.product_ids, filter_fields.product_category_ids)
        internal_picking_type = self._get_internal_picking_type(is_groupby_location)

        df = _date(date_from)
        dt = _date(date_to)
        loc = _ids(locations)
        prd = _ids(product_ids)
        cat = _ids(product_category_ids)

        if count_internal_transfer:
            query_ = """
                SELECT *, (a.initial + a.product_in - a.product_out) AS balance,
                    (a.initial_amount + a.product_in_amount - a.product_out_amount) AS amount
                FROM (
                    SELECT row_number() OVER () AS id,
                        mg.product_id, mg.product_uom, mg.location, mg.product_category,
                        (sum(CASE WHEN CAST(mg.date AS date) < {df}
                                AND mg.location = mg.location_dest_id
                             THEN mg.product_qty ELSE 0 END)
                        - sum(CASE WHEN CAST(mg.date AS date) < {df}
                                AND mg.location = mg.location_id
                             THEN mg.product_qty ELSE 0 END)) AS initial,
                        (sum(CASE WHEN CAST(mg.date AS date) < {df}
                                AND mg.location = mg.location_dest_id
                             THEN mg.product_qty * mg.unit_cost ELSE 0 END)
                        - sum(CASE WHEN CAST(mg.date AS date) < {df}
                                AND mg.location = mg.location_id
                             THEN mg.product_qty * mg.unit_cost ELSE 0 END)) AS initial_amount,
                        sum(CASE WHEN CAST(mg.date AS date) >= {df}
                                AND mg.location = mg.location_dest_id
                             THEN mg.product_qty ELSE 0 END) AS product_in,
                        sum(CASE WHEN CAST(mg.date AS date) >= {df}
                                AND mg.location = mg.location_dest_id
                             THEN mg.product_qty * mg.unit_cost ELSE 0 END) AS product_in_amount,
                        sum(CASE WHEN CAST(mg.date AS date) >= {df}
                                AND mg.location = mg.location_id
                             THEN mg.product_qty ELSE 0 END) AS product_out,
                        sum(CASE WHEN CAST(mg.date AS date) >= {df}
                                AND mg.location = mg.location_id
                             THEN mg.product_qty * mg.unit_cost ELSE 0 END) AS product_out_amount
                    FROM (
                        SELECT move.date, move.product_id, move.product_uom,
                            move.location_id AS location,
                            move.location_id, move.location_dest_id,
                            template.categ_id AS product_category,
                            move.product_qty,
                            {uc} AS unit_cost
                        FROM stock_move move
                            LEFT JOIN stock_location location_src ON move.location_id = location_src.id
                            LEFT JOIN product_product product ON move.product_id = product.id
                            LEFT JOIN product_template template ON product.product_tmpl_id = template.id
                        WHERE move.location_id IN {loc}
                            AND move.state = 'done'
                            AND move.product_id IN {prd}
                            AND template.categ_id IN {cat}
                            AND CAST(move.date AS date) <= {dt}
                            AND location_src.usage = 'internal'
                        UNION ALL
                        SELECT move.date, move.product_id, move.product_uom,
                            move.location_dest_id AS location,
                            move.location_id, move.location_dest_id,
                            template.categ_id AS product_category,
                            move.product_qty,
                            {uc} AS unit_cost
                        FROM stock_move move
                            LEFT JOIN stock_location location_dest ON move.location_dest_id = location_dest.id
                            LEFT JOIN product_product product ON move.product_id = product.id
                            LEFT JOIN product_template template ON product.product_tmpl_id = template.id
                        WHERE move.location_dest_id IN {loc}
                            AND move.state = 'done'
                            AND move.product_id IN {prd}
                            AND template.categ_id IN {cat}
                            AND CAST(move.date AS date) <= {dt}
                            AND location_dest.usage = 'internal'
                    ) AS mg
                    GROUP BY mg.product_id, mg.product_uom, mg.location, mg.product_category
                    ORDER BY mg.product_id, mg.product_uom, mg.location, mg.product_category
                ) AS a
            """.format(df=df, dt=dt, loc=loc, prd=prd, cat=cat, uc=_UNIT_COST)
        else:
            ipt = _ids(internal_picking_type)
            query_ = """
                SELECT *, (a.initial + a.product_in - a.product_out) AS balance,
                    (a.initial_amount + a.product_in_amount - a.product_out_amount) AS amount
                FROM (
                    SELECT row_number() OVER () AS id,
                        move.product_id, move.product_uom,
                        NULL AS location,
                        template.categ_id AS product_category,
                        (sum(CASE WHEN CAST(move.date AS date) < {df}
                                AND location_dest.usage = 'internal'
                             THEN move.product_qty ELSE 0 END)
                        - sum(CASE WHEN CAST(move.date AS date) < {df}
                                AND location.usage = 'internal'
                             THEN move.product_qty ELSE 0 END)) AS initial,
                        (sum(CASE WHEN CAST(move.date AS date) < {df}
                                AND location_dest.usage = 'internal'
                             THEN move.product_qty * {uc} ELSE 0 END)
                        - sum(CASE WHEN CAST(move.date AS date) < {df}
                                AND location.usage = 'internal'
                             THEN move.product_qty * {uc} ELSE 0 END)) AS initial_amount,
                        sum(CASE WHEN CAST(move.date AS date) >= {df}
                                AND location_dest.usage = 'internal'
                             THEN move.product_qty ELSE 0 END) AS product_in,
                        sum(CASE WHEN CAST(move.date AS date) >= {df}
                                AND location_dest.usage = 'internal'
                             THEN move.product_qty * {uc} ELSE 0 END) AS product_in_amount,
                        sum(CASE WHEN CAST(move.date AS date) >= {df}
                                AND location.usage = 'internal'
                             THEN move.product_qty ELSE 0 END) AS product_out,
                        sum(CASE WHEN CAST(move.date AS date) >= {df}
                                AND location.usage = 'internal'
                             THEN move.product_qty * {uc} ELSE 0 END) AS product_out_amount
                    FROM stock_move move
                        LEFT JOIN stock_location location ON move.location_id = location.id
                        LEFT JOIN stock_location location_dest ON move.location_dest_id = location_dest.id
                        LEFT JOIN product_product product ON move.product_id = product.id
                        LEFT JOIN product_template template ON product.product_tmpl_id = template.id
                    WHERE (move.location_id IN {loc} OR move.location_dest_id IN {loc})
                        AND (move.picking_type_id NOT IN {ipt} OR move.picking_type_id IS NULL)
                        AND move.state = 'done'
                        AND move.product_id IN {prd}
                        AND template.categ_id IN {cat}
                        AND CAST(move.date AS date) <= {dt}
                    GROUP BY move.product_id, move.product_uom, template.categ_id
                    ORDER BY move.product_id
                ) AS a
            """.format(df=df, dt=dt, loc=loc, prd=prd, cat=cat, ipt=ipt, uc=_UNIT_COST)

        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("CREATE VIEW {} AS ({})".format(self._table, query_))

    def action_update_onhand_qty(self):
        """Update stock.quant to match the move-based balance for each row."""
        updated = 0
        for rec in self:
            if not rec.product_id or not rec.location:
                continue
            quant = self.env['stock.quant'].search([
                ('product_id', '=', rec.product_id.id),
                ('location_id', '=', rec.location.id),
            ], limit=1)
            if quant:
                quant.sudo().write({'quantity': rec.balance})
            else:
                self.env['stock.quant'].sudo().create({
                    'product_id': rec.product_id.id,
                    'location_id': rec.location.id,
                    'quantity': rec.balance,
                })
            updated += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'On-Hand Qty Updated',
                'message': f'{updated} product(s) on-hand qty updated from move-based balance.',
                'type': 'success',
                'sticky': False,
            },
        }

    def report_details(self):
        filters = self._context.get("filters")
        filters["product_ids"] = [(6, 0, self.product_id.ids)]
        report = self.env["imex.inventory.report.wizard"].create(
            self._context.get("filters"))
        self.env["imex.inventory.details.report"].init_results(report)
        details = self.env["imex.inventory.details.report"].search([])
        action = self.env.ref(
            'imex_inventory_report.action_imex_inventory_details_report')
        vals = action.sudo().read()[0]
        context = vals.get("context", {})
        if context:
            context = safe_eval(context)
        context["active_ids"] = details.ids
        data = {
            'product_default_code': report.product_ids.default_code,
            'product_name': report.product_ids.name,
            'date_from': report.date_from or None,
            'date_to': report.date_to or fields.Date.context_today(self),
            'location': report.location_id.complete_name or None,
            'category': report.product_ids.categ_id.complete_name or None,
        }
        context["data"] = data
        vals["context"] = context
        return vals
