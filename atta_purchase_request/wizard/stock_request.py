from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class StockRequestWizard(models.TransientModel):
    _name = 'stock.request.wizard'
    _description = 'Create Stock Request Wizard'

    expected_date = fields.Datetime(
        default=fields.Datetime.now,
        index=True,
        required=True,
        readonly=False,
        help="Date when you expect to receive the goods.",
    )
    picking_policy = fields.Selection(
        [
            ("direct", "Receive each product when available"),
            ("one", "Receive all products at once"),
        ],
        string="Shipping Policy",
        required=True,
        readonly=False,
        default="direct",
    )
    warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Warehouse",
        readonly=False,
        ondelete="cascade",
        required=True,
    )
    allow_virtual_location = fields.Boolean(
        related="company_id.stock_request_allow_virtual_loc", readonly=True
    )
    location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Location",
        domain="not allow_virtual_location and "
               "[('usage', 'in', ['internal', 'transit'])] or []",
        readonly=False,
        ondelete="cascade",
        required=True,
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )

    @api.onchange("warehouse_id")
    def onchange_warehouse_id(self):
        if self.warehouse_id:
            # search with sudo because the user may not have permissions
            loc_wh = self.location_id.warehouse_id
            if self.warehouse_id != loc_wh:
                self.location_id = self.warehouse_id.lot_stock_id


    def action_create_stock_request(self):
        purchase_request_line_ids = self.env['purchase.request.line'].browse(self._context.get('request_line_ids'))
        for line in purchase_request_line_ids:
            line.write({'state_creation': 'stock'})
            if line.stock_request_id:
                raise ValidationError(_('Stock Request Is Already Created for ' + line.product_id.name))
            if line.order_line_ids:
                raise ValidationError(_('Purchase RFQ/PO Is Already Created for ' + line.product_id.name))
            if line.expense_transfer_id:
                raise ValidationError(_('Expense Is Already Created for ' + line.product_id.name))
        for line in purchase_request_line_ids:
            stock_request_id = self.env['stock.request'].create(
                {
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_id.uom_id.id,
                    'product_uom_qty': line.request_qty,
                    'expected_date': self.expected_date,
                    'picking_policy': self.picking_policy,
                    'warehouse_id': self.warehouse_id.id,
                    'location_id': self.location_id.id,
                    'company_id': self.company_id.id,
                })
            line.stock_request_id = stock_request_id.id
