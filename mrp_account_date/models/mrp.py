from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    accounting_date = fields.Date('Accounting Date')
    is_customer_required = fields.Boolean(string="Customer Required", compute="_compute_is_customer_required", store=True)
    partner_id = fields.Many2one('res.partner', string="Customer")

    @api.depends('product_id')
    def _compute_is_customer_required(self):
        for order in self:
            if order.product_id.categ_id.is_customer_required:
                order.is_customer_required = True
            else:
                order.is_customer_required = False

    def button_mark_done(self):
        not_avlible_line_ids = self.move_raw_ids.filtered(lambda x:x.forecast_availability < x.product_uom_qty)
        bom_product_ids = self.bom_id.bom_line_ids.filtered(lambda x:x.type_component == 'material_cost').mapped('product_id')
        not_avlible_product_ids = not_avlible_line_ids.mapped('product_id')
        common_product_ids = bom_product_ids & not_avlible_product_ids
        if common_product_ids:
            # Get product names and join them with a comma
            product_names_no_qty = ", ".join(common_product_ids.mapped('name'))
            # Raise a validation error with the product names
            raise ValidationError(f"The following products have no Reserverd quantity: {product_names_no_qty}")
        self.with_context({
            'mo_accounting_date': self.accounting_date,
        })
        res = super(MrpProduction, self).button_mark_done()
        return res

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, values):
        if self.env.context.get('mo_accounting_date'):
            values.update({'date': self.env.context.get('mo_accounting_date')})
        res = super(AccountMove, self).create(values)
        if self.env.context.get('mo_accounting_date'):
            res.action_prepost()
        return res

class ProductCategory(models.Model):
    _inherit = 'product.category'

    is_customer_required = fields.Boolean(string="Customer Required")

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_partner_id_for_valuation_lines(self):
        print("jjjjjjjjjjjj", self.raw_material_production_id.partner_id.id)
        print((self.picking_id.partner_id and self.env['res.partner']._find_accounting_partner(self.picking_id.partner_id).id) or False, "lll")
        if self.raw_material_production_id.partner_id:
            return self.raw_material_production_id.partner_id.id
        else:
            return (self.picking_id.partner_id and self.env['res.partner']._find_accounting_partner(self.picking_id.partner_id).id) or False
