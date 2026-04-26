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
        for production in self:
            not_avlible_line_ids = production.move_raw_ids.filtered(
                lambda move: move.forecast_availability < move.product_uom_qty)
            bom_lines = production.bom_id.bom_line_ids
            # Odoo 19 migration: type_component is a custom field from process costing and may not exist.
            # Old direct filter kept for migration reference:
            # bom_product_ids = production.bom_id.bom_line_ids.filtered(lambda x: x.type_component == 'material_cost').mapped('product_id')
            if 'type_component' in bom_lines._fields:
                bom_product_ids = bom_lines.filtered(lambda line: line.type_component == 'material_cost').mapped('product_id')
            else:
                bom_product_ids = bom_lines.mapped('product_id')
            not_avlible_product_ids = not_avlible_line_ids.mapped('product_id')
            common_product_ids = bom_product_ids & not_avlible_product_ids
            if common_product_ids:
                product_names_no_qty = ", ".join(common_product_ids.mapped('name'))
                raise ValidationError(_("The following products have no reserved quantity: %s") % product_names_no_qty)
        accounting_date = self[:1].accounting_date
        if accounting_date:
            return super(MrpProduction, self.with_context(
                force_period_date=accounting_date,
                mo_accounting_date=accounting_date,
            )).button_mark_done()
        return super(MrpProduction, self).button_mark_done()

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model_create_multi
    def create(self, vals_list):
        mo_accounting_date = self.env.context.get('mo_accounting_date') or self.env.context.get('force_period_date')
        if mo_accounting_date:
            for values in vals_list:
                values['date'] = mo_accounting_date
        res = super(AccountMove, self).create(vals_list)
        # Odoo 19 migration: account.move.action_prepost() no longer exists.
        # Stock valuation moves are posted by stock_account after creation.
        # Old code kept for migration reference:
        # if self.env.context.get('mo_accounting_date'):
        #     res.action_prepost()
        return res

class ProductCategory(models.Model):
    _inherit = 'product.category'

    is_customer_required = fields.Boolean(string="Customer Required")

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_account_move_line_vals(self):
        vals_list = super()._get_account_move_line_vals()
        partner_id = self._get_partner_id_for_valuation_lines()
        if partner_id:
            for vals in vals_list:
                vals['partner_id'] = partner_id
        return vals_list

    def _get_partner_id_for_valuation_lines(self):
        production = self.raw_material_production_id or self.production_id
        if production.partner_id:
            return production.partner_id.id
        return (self.picking_id.partner_id and self.env['res.partner']._find_accounting_partner(self.picking_id.partner_id).id) or False
