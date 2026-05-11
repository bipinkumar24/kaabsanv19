from odoo import api, fields, models, tools
from odoo.tools.safe_eval import safe_eval
from odoo.tools.mail import is_html_empty

# stock.valuation.layer was removed in Odoo 19.
_UNIT_COST = (
    "COALESCE(NULLIF(move.price_unit, 0),"
    " CASE WHEN move.quantity != 0 THEN ABS(move.value / move.quantity) ELSE 0 END,"
    " 0)"
)


def _ids(t):
    return "({})".format(",".join(str(int(i)) for i in t)) if t else "(-1)"


def _date(d):
    return "'{}'".format(str(d))


class StockMove(models.Model):
    _inherit = "stock.move"

    move_picking_type_id = fields.Many2one(related="picking_id.picking_type_id", store=True)


class ImexInventoryDetailsReport(models.Model):
    _name = "imex.inventory.details.report"
    _description = "Imex Inventory Details Report"
    _auto = False

    date = fields.Datetime(readonly=True)
    product_id = fields.Many2one(comodel_name="product.product", readonly=True)
    product_qty = fields.Float(readonly=True)
    product_uom = fields.Many2one(comodel_name="uom.uom", readonly=True)
    product_category = fields.Many2one(
        comodel_name="product.category", readonly=True, related="product_id.categ_id")
    unit_cost = fields.Float(readonly=True, digits=(16, 4))
    reference = fields.Char(readonly=True)
    partner_id = fields.Many2one(comodel_name="res.partner", readonly=True)
    origin = fields.Char(readonly=True)
    location_id = fields.Many2one(comodel_name="stock.location", readonly=True)
    location_dest_id = fields.Many2one(comodel_name="stock.location", readonly=True)
    initial = fields.Float(readonly=True)
    initial_amount = fields.Float(readonly=True)
    product_in = fields.Float(readonly=True)
    product_out = fields.Float(readonly=True)
    picking_id = fields.Many2one(comodel_name="stock.picking", readonly=True)

    def _compute_display_name(self):
        for rec in self:
            name = rec.reference or ''
            if rec.picking_id and rec.picking_id.origin:
                name = "{} ({})".format(name, rec.picking_id.origin)
            rec.display_name = name

    def _get_locations(self, location_id, is_groupby_location):
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
        return locations

    def init_results(self, filter_fields):
        date_from = filter_fields.date_from or "1900-01-01"
        date_to = filter_fields.date_to or fields.Date.context_today(self)
        is_groupby_location = filter_fields.is_groupby_location

        locations = self._get_locations(filter_fields.location_id, is_groupby_location)
        product_ids = tuple(filter_fields.product_ids.ids) or (-1,)

        loc = _ids(locations)
        prd = _ids(product_ids)
        df = _date(date_from)
        dt = _date(date_to)

        query = """
            CREATE OR REPLACE VIEW imex_inventory_details_report AS (
                SELECT
                    row_number() OVER () AS id,
                    line.date             AS date,
                    line.product_id       AS product_id,
                    line.quantity         AS product_qty,
                    line.product_uom_id   AS product_uom,
                    {uc}                  AS unit_cost,
                    move.reference        AS reference,
                    move.partner_id       AS partner_id,
                    move.origin           AS origin,
                    line.location_id      AS location_id,
                    line.location_dest_id AS location_dest_id,
                    100 AS initial,
                    200 AS initial_amount,
                    CASE WHEN line.location_dest_id IN {loc} THEN line.quantity ELSE 0 END AS product_in,
                    CASE WHEN line.location_id      IN {loc} THEN line.quantity ELSE 0 END AS product_out,
                    move.picking_id AS picking_id
                FROM stock_move_line line
                LEFT JOIN stock_move move ON move.id = line.move_id
                WHERE line.state = 'done'
                  AND (move.location_id IN {loc} OR move.location_dest_id IN {loc})
                  AND line.product_id IN {prd}
                  AND CAST(line.date AS date) >= {df}
                  AND CAST(line.date AS date) <= {dt}
            )
        """.format(uc=_UNIT_COST, loc=loc, prd=prd, df=df, dt=dt)

        tools.drop_view_if_exists(self._cr, 'imex_inventory_details_report')
        self._cr.execute(query)

    def print_report(self):
        action = self.env.ref(
            "imex_inventory_report.action_imex_inventory_details_report_pdf")
        vals = action.sudo().read()[0]
        context = vals.get("context", {})
        if context:
            context = safe_eval(context)
        context["active_ids"] = self._context.get("active_ids")
        context["details"] = self.browse(self._context.get("active_ids"))
        vals["data"] = self._context.get("data")
        vals["context"] = context
        return vals

    def _get_html(self):
        rcontext = {}
        report = self.browse(self._context.get("active_ids"))
        data = self._context.get("data")
        if report:
            date_records = report.filtered(lambda r: r.date)
            not_date_records = report.filtered(lambda r: not r.date)
            sorted_records = date_records.sorted(key=lambda r: r.date)
            main_record = not_date_records + sorted_records
            rcontext["details"] = main_record
            rcontext["data"] = data
            rcontext["is_html_empty"] = is_html_empty
            return {'html': self.env['ir.qweb']._render(
                'imex_inventory_report.imex_inventory_details_report', rcontext)}
        return {}

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(**(given_context or {}))._get_html()
