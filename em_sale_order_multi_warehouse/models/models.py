# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from odoo.tools import float_compare


class InheritSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_on_warehouse_ids = fields.One2many('product.on.warehouse', 'sale_line_id')

    def unset_product_on_warehouse_ids(self):
        self.product_on_warehouse_ids = False

    def set_product_on_warehouse_ids(self):
        if self.product_uom_qty > 0:
            product_on_warehouse_ids = []
            ircsudo = self.env['ir.config_parameter'].sudo()
            auto_fill = bool(ircsudo.get_param('sale_with_order_history.auto_fill'))

            self.product_on_warehouse_ids = False
            assigned_qty = 0
            for warehouse_id in self.env['stock.warehouse'].search([]):
                stock_quant_ids = self.env['stock.quant'].search(
                    [('location_id', 'child_of', warehouse_id.view_location_id.id),
                     ('product_id', '=', self.product_id.id),
                     ('quantity', '>=', 0)])
                order_qty, assigned_qty = self.get_suitable_quantity(warehouse_id, assigned_qty) if auto_fill else (
                0, 0)
                product_on_warehouse_ids.append((0, 0, {
                    "warehouse_id": warehouse_id.id,
                    "available_qty": sum(stock_quant_ids.mapped('quantity')),
                    "order_qty": order_qty if auto_fill else 0,
                }))
            self.product_on_warehouse_ids = product_on_warehouse_ids
        else:
            self.unset_product_on_warehouse_ids()

    @api.onchange('product_uom_qty')
    def onchange_product_uom_qty_set_wh_qty(self):
        if self.product_on_warehouse_ids:
            self.set_product_on_warehouse_ids()

    def show_form_view(self):
        if self.order_id.state == 'draft' and self.env.context.get("compute_pows", False):
            self.set_product_on_warehouse_ids()
        view_id = self.env.ref('em_sale_order_multi_warehouse.sale_order_line_for_product_on_warehouse')
        return {
            'name': "Sale Order Line",
            'view_mode': 'form',
            'view_id': self.env.ref('em_sale_order_multi_warehouse.sale_order_line_for_product_on_warehouse').id,
            'res_model': 'sale.order.line',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }

    def get_suitable_quantity(self, warehouse_id, assigned_qty):
        ircsudo = self.env['ir.config_parameter'].sudo()
        auto_fill = bool(ircsudo.get_param('sale_with_order_history.auto_fill'))
        total_qty = sum(self.env['stock.quant'].search(
            [('product_id', '=', self.product_id.id),
             ('quantity', '>=', 0)]).mapped('quantity'))
        wh_total_qty = sum(self.env['stock.quant'].search(
            [('location_id', 'child_of', warehouse_id.view_location_id.id), ('product_id', '=', self.product_id.id),
             ('quantity', '>=', 0)]).mapped('quantity'))
        wh_qty_per = round(wh_total_qty * 100 / total_qty)
        qty_from_wh = round(self.product_uom_qty * wh_qty_per / 100)
        want_wh_qty = auto_fill and (assigned_qty < self.product_uom_qty) and (
                self.product_uom_qty == round(self.product_uom_qty))
        assigned_qty += qty_from_wh
        return (qty_from_wh, assigned_qty) if want_wh_qty else (0, assigned_qty)

    def save_data(self):
        balanced_qty_list = []
        for pow in self.product_on_warehouse_ids:
            balanced_qty_list.append(pow.available_qty >= pow.order_qty)
        is_qty_balanced_with_wh = all(balanced_qty_list)
        order_qty = sum(self.product_on_warehouse_ids.mapped('order_qty'))
        if self.product_uom_qty != order_qty or not is_qty_balanced_with_wh:
            self.product_on_warehouse_ids = False
            raise ValidationError('Product quantity not distributed for warehouses properly. Try Again!')

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        if self.env.context.get("skip_procurement"):
            return True

        precision = self.env['decimal.precision'].precision_get('Product Unit')
        procurements = []

        for line in self:
            line = line.with_company(line.company_id)

            if line.state != 'sale' or line.order_id.locked:
                continue

            # Skip services
            if line.product_id.type not in ['product', 'consu']:
                continue

            qty_already_procured = line._get_qty_procurement(previous_product_uom_qty)

            if float_compare(qty_already_procured, line.product_uom_qty, precision_digits=precision) == 0:
                continue

            references = line.order_id.stock_reference_ids
            if not references:
                self.env['stock.reference'].create(line._prepare_reference_vals())

            if not line.product_on_warehouse_ids:
                values = line._prepare_procurement_values()
                product_qty = line.product_uom_qty - qty_already_procured

                product_qty, procurement_uom = line.product_uom_id._adjust_uom_quantities(
                    product_qty,
                    line.product_id.uom_id
                )

                procurements += line._create_procurements(
                    product_qty,
                    procurement_uom,
                    values
                )
                continue

            for wh_line in line.product_on_warehouse_ids:

                if not wh_line.order_qty:
                    continue

                values = line._prepare_procurement_values()

                values.update({
                    'warehouse_id': wh_line.warehouse_id,
                })

                product_qty = wh_line.order_qty

                product_qty, procurement_uom = line.product_uom_id._adjust_uom_quantities(
                    product_qty,
                    line.product_id.uom_id
                )

                procurements += line._create_procurements(
                    product_qty,
                    procurement_uom,
                    values
                )

        if procurements:
            self.env['stock.rule'].run(procurements)

        # Confirm pickings
        orders = self.mapped('order_id')
        for order in orders:
            pickings_to_confirm = order.picking_ids.filtered(
                lambda p: p.state not in ['cancel', 'done']
            )
            if pickings_to_confirm:
                pickings_to_confirm.action_confirm()

        return True

class ProductOnWarehouse(models.Model):
    _name = 'product.on.warehouse'

    warehouse_id = fields.Many2one('stock.warehouse', required=True)
    available_qty = fields.Float()
    order_qty = fields.Float()
    sale_line_id = fields.Many2one('sale.order.line')

class ResCompany(models.Model):
    _inherit = "res.company"

    auto_fill = fields.Boolean()

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    auto_fill = fields.Boolean(related='company_id.auto_fill',
        string="Auto Fill",
        readonly=False)
