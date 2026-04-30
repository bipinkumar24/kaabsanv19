# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_round

class AccountMove(models.Model):
    _inherit = "account.move"

    mrp_production_id = fields.Many2one('mrp.production')

class MrpBom(models.Model):
    _inherit = "mrp.bom"

    def _compute_total_cost(self):
        material_total = 0.0
        labour_total = 0.0
        overhead_total = 0.0
        for line in self.bom_material_cost_ids:
            material_total += line.total_cost

        for line in self.bom_labour_cost_ids:
            labour_total += line.total_cost

        for line in self.bom_overhead_cost_ids:
            overhead_total += line.total_cost

        self.bom_total_material_cost = material_total
        self.bom_total_labour_cost = labour_total
        self.bom_total_overhead_cost = overhead_total

    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id

    @api.model_create_multi
    def create(self, vals_list):
        res = super(MrpBom, self).create(vals_list)
        for res in res:
            for vals in vals_list:
                for material in res.bom_line_ids:
                    if not material.product_id.standard_price:
                        raise UserError(_(material.product_id.name + " Enter This Product Cost!"))

                    vals_material = {
                        'product_id': material.product_id.product_tmpl_id.id,
                        'product_product_id': material.product_id.id,
                        'planned_qty': material.product_qty,
                        'uom_id': material.product_uom_id.id,
                        'cost': material.product_id.standard_price,
                        'mrp_bom_material_id': res.id,
                        'mrp_bom_line_id': material.id,

                    }

                    vals_labour = {
                        'product_id': material.product_id.product_tmpl_id.id,
                        'product_product_id': material.product_id.id,
                        'planned_qty': material.product_qty,
                        'uom_id': material.product_uom_id.id,
                        'cost': material.product_id.standard_price,
                        'mrp_bom_labour_id': res.id,
                        'mrp_bom_line_id': material.id,
                    }

                    vals_overhead = {
                        'product_id': material.product_id.product_tmpl_id.id,
                        'product_product_id': material.product_id.id,
                        'planned_qty': material.product_qty,
                        'uom_id': material.product_uom_id.id,
                        'cost': material.product_id.standard_price,
                        'mrp_bom_overhead_id': res.id,
                        'mrp_bom_line_id': material.id,
                    }

                    if material.type_component == 'material_cost':
                        res.write({'bom_material_cost_ids': [(0, 0, vals_material)]})
                    elif material.type_component == 'labour_cost':
                        res.write({'bom_labour_cost_ids': [(0, 0, vals_labour)]})
                    else:
                        res.write({'bom_overhead_cost_ids': [(0, 0, vals_overhead)]})
                config = self.env['res.config.settings'].search([], order="id desc", limit=1)
                if res.operation_ids and config.process_costing == 'workcenter':
                    for line in res.bom_labour_cost_ids:
                        line.unlink()
                    for line in res.bom_overhead_cost_ids:
                        line.unlink()
                    for operation in res.operation_ids:
                        value = {
                            'operation_id': operation.id,
                            'workcenter_id': operation.workcenter_id.id,
                            'cost': operation.workcenter_id.labour_costs_hour or False,
                            'mrp_bom_labour_id': res.id,
                        }
                        if operation.time_cycle > 0:
                            value.update({'planned_qty': operation.time_cycle / 60})
                        res.write({'bom_labour_cost_ids': [(0, 0, value)]})

                    for operation in res.operation_ids:
                        value = {
                            'operation_id': operation.id,
                            'workcenter_id': operation.workcenter_id.id,
                            'cost': operation.workcenter_id.overhead_cost_hour or False,
                            'mrp_bom_overhead_id': res.id,

                        }
                        if operation.time_cycle > 0:
                            value.update({'planned_qty': operation.time_cycle / 60})
                        res.write({'bom_overhead_cost_ids': [(0, 0, value)]})
        return res

    def write(self, vals):
        res = super(MrpBom, self).write(vals)
        if vals.get('bom_line_ids'):
            for line in self.bom_material_cost_ids:
                line.unlink()
            for material in self.bom_line_ids:
                if not material.product_id.standard_price:
                    raise UserError(_(material.product_id.name + " Enter This Product Cost!"))
                vals_material = {
                    'product_id': material.product_id.product_tmpl_id.id,
                    'product_product_id': material.product_id.id,
                    'planned_qty': material.product_qty,
                    'uom_id': material.product_uom_id.id,
                    'cost': material.product_id.standard_price,
                    'mrp_bom_material_id': self.id,
                    'mrp_bom_line_id': material.id,
                }

                vals_labour = {
                    'product_id': material.product_id.product_tmpl_id.id,
                    'product_product_id': material.product_id.id,
                    'planned_qty': material.product_qty,
                    'uom_id': material.product_uom_id.id,
                    'cost': material.product_id.standard_price,
                    'mrp_bom_labour_id': self.id,
                    'mrp_bom_line_id': material.id,
                }

                vals_overhead = {
                    'product_id': material.product_id.product_tmpl_id.id,
                    'product_product_id': material.product_id.id,
                    'planned_qty': material.product_qty,
                    'uom_id': material.product_uom_id.id,
                    'cost': material.product_id.standard_price,
                    'mrp_bom_overhead_id': self.id,
                    'mrp_bom_line_id': material.id,
                }
                if material.type_component == 'material_cost':
                    mrp_bom_material_cost_id = self.env['mrp.bom.material.cost'].search([('mrp_bom_line_id', '=', material.id)])
                    if mrp_bom_material_cost_id:
                        mrp_bom_material_cost_id.write(vals_material)
                    else:
                        self.env['mrp.bom.material.cost'].create(vals_material)
                elif material.type_component == 'labour_cost':
                    mrp_bom_labour_cost_id = self.env['mrp.bom.labour.cost'].search([('mrp_bom_line_id', '=', material.id)])
                    if mrp_bom_labour_cost_id:
                        mrp_bom_labour_cost_id.write(vals_labour)
                    else:
                        self.env['mrp.bom.labour.cost'].create(vals_labour)
                else:
                    mrp_bom_overhead_cost_id = self.env['mrp.bom.overhead.cost'].search([('mrp_bom_line_id', '=', material.id)])
                    if mrp_bom_overhead_cost_id:
                        mrp_bom_overhead_cost_id.write(vals_overhead)
                    else:
                        self.env['mrp.bom.overhead.cost'].create(vals_overhead)
        config = self.env['res.config.settings'].search([], order="id desc", limit=1)
        check_condition = vals.get('operation_ids') and config.process_costing == 'workcenter'
        if check_condition:
            for line in self.bom_labour_cost_ids:
                line.unlink()
            for line in self.bom_overhead_cost_ids:
                line.unlink()
            total = 0
            for operation in self.operation_ids:
                total += 1
                value = {
                    'operation_id': operation.id,
                    'workcenter_id': operation.workcenter_id.id,
                    'cost': operation.workcenter_id.labour_costs_hour or False,
                    'mrp_bom_labour_id': self.id,
                }
                if operation.time_cycle > 0:
                    value.update({'planned_qty': operation.time_cycle / 60})
                self.write({'bom_labour_cost_ids': [(0, 0, value)]})

            for operation in self.operation_ids:
                value = {
                    'operation_id': operation.id,
                    'workcenter_id': operation.workcenter_id.id,
                    'cost': operation.workcenter_id.overhead_cost_hour or False,
                    'mrp_bom_overhead_id': self.id,
                }
                if operation.time_cycle > 0:
                    value.update({'planned_qty': operation.time_cycle / 60})
                self.write({'bom_overhead_cost_ids': [(0, 0, value)]})

        return res

    bom_material_cost_ids = fields.One2many("mrp.bom.material.cost", "mrp_bom_material_id", "Material Cost")
    bom_labour_cost_ids = fields.One2many("mrp.bom.labour.cost", "mrp_bom_labour_id", "Labour Cost")
    bom_overhead_cost_ids = fields.One2many("mrp.bom.overhead.cost", "mrp_bom_overhead_id", "Overhead Cost")
    bom_total_material_cost = fields.Float(compute='_compute_total_cost', string="Total Material Cost", default=0.0)
    bom_total_labour_cost = fields.Float(compute='_compute_total_cost', string="Total Labour Cost", default=0.0)
    bom_total_overhead_cost = fields.Float(compute='_compute_total_cost', string="Total Overhead Cost", default=0.0)
    currency_id = fields.Many2one("res.currency", compute='get_currency_id', string="Currency")


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    type_component = fields.Selection([('material_cost', 'Material Cost'),
                                       ('labour_cost', 'Labour Cost'),
                                       ('overhead_cost', 'Overhead Cost')], string='Type of Component')

    def write(self, vals):
        if vals.get('product_id'):
            product = self.env['product.product'].browse(vals.get('product_id'))
            old_product = self.product_id.product_tmpl_id
            product_id = product.product_tmpl_id
            material_product_id = self.env['mrp.bom.material.cost'].search(
                [('product_id', '=', old_product.id), ('mrp_bom_material_id', '=', self.bom_id.id)])
            material_vals = {
                'product_id': product_id.id,
                'uom_id': product_id.uom_id.id,
                'cost': product_id.uom_id._compute_price(product_id.standard_price, product_id.uom_id),
                'planned_qty': self.product_qty or vals.get('product_qty'),
            }
            material_product_id.write(material_vals)
        if vals.get('product_qty'):
            product = self.env['product.product'].browse(self.product_id)
            product_id = self.product_id.product_tmpl_id
            material_product_id = self.env['mrp.bom.material.cost'].search(
                [('product_id', '=', product_id.id), ('mrp_bom_material_id', '=', self.bom_id.id)])
            material_product_id.write({'planned_qty': vals.get('product_qty')})

        res = super(MrpBomLine, self).write(vals)
        return res


class MrpBomMaterialCost(models.Model):
    _name = "mrp.bom.material.cost"
    _description = "MRP BOM MATERIAL COST"

    operation_id = fields.Many2one('mrp.routing.workcenter', string="Operation")
    product_id = fields.Many2one('product.template', string="Product")
    product_product_id = fields.Many2one('product.product', string="Product")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.relative_uom_id', depends=['product_id'])
    planned_qty = fields.Float(string="Planned Qty", default=0.0)
    actual_qty = fields.Float(string="Actual Qty", default=0.0)
    uom_id = fields.Many2one('uom.uom', string="UOM",domain="[('relative_uom_id', '=', product_uom_category_id)]")
    cost = fields.Float(string="Cost/Unit")
    total_cost = fields.Float(compute='onchange_planned_qty', string="Total Cost")
    total_actual_cost = fields.Float(compute='onchange_planned_qty', string="Total Actual Cost")
    mrp_bom_material_id = fields.Many2one("mrp.bom", "Mrp Bom Material")
    mrp_pro_material_id = fields.Many2one("mrp.production", "Mrp Production Material")
    mrp_wo_material_id = fields.Many2one("mrp.workorder", "Mrp Workorder Material")
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    pricelist_item_id = fields.Many2one(
        comodel_name='product.pricelist.item',
        compute='_compute_pricelist_item_id')
    product_no_variant_attribute_value_ids = fields.Many2many(
        comodel_name='product.template.attribute.value',
        string="Extra Values",
        compute='_compute_no_variant_attribute_values',
        store=True, readonly=False, precompute=True, ondelete='restrict')
    mrp_bom_line_id = fields.Many2one("mrp.bom.line", "Mrp Bom Line")

    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if not self.product_id:
            return res
        self.uom_id = self.product_id.uom_id.id
        if self.uom_id:
            self.cost = self.product_id.uom_id._compute_price(self.product_id.standard_price, self.uom_id)
        else:
            self.cost = self.product_id.uom_id._compute_price(self.product_id.standard_price, self.product_id.uom_id)

    @api.depends('product_id', 'uom_id', 'planned_qty')
    def _compute_pricelist_item_id(self):
        for line in self:
            if not line.product_id or not line.mrp_pro_material_id.pricelist_id:
                line.pricelist_item_id = False
            else:
                set_product = line.product_id.product_variant_id
                line.pricelist_item_id = line.mrp_pro_material_id.pricelist_id._get_product_rule(
                    set_product,
                    line.planned_qty or 1.0,
                    uom=line.uom_id,
                    date=line.mrp_pro_material_id.create_date,
                )

    def _get_pricelist_price(self):
        self.ensure_one()
        price = 0
        if self.product_id:
            self.product_id.ensure_one()
            pricelist_rule = self.pricelist_item_id
            order_date = self.mrp_pro_material_id.create_date or fields.Date.today()
            set_product = self.product_id.product_variant_id
            product = set_product.with_context(**self._get_product_price_context())
            qty = self.planned_qty or 1.0
            uom = self.uom_id or set_product.uom_id
            price = False
            if self.currency_id:
                price = pricelist_rule._compute_price(
                    product, qty, uom, order_date, currency=self.currency_id)
        return price

    def _get_display_price(self):
        for rec in self:
            rec.ensure_one()
            pricelist_price = rec._get_pricelist_price()
            if not self.pricelist_item_id:
                return pricelist_price
        return max(pricelist_price)

    def _get_product_price_context(self):
        self.ensure_one()
        res = {}
        no_variant_attributes_price_extra = [
            ptav.price_extra for ptav in self.product_no_variant_attribute_value_ids.filtered(
                lambda ptav: ptav.price_extra and ptav not in self.product_id.product_template_attribute_value_ids
            )
        ]
        if no_variant_attributes_price_extra:
            res['no_variant_attributes_price_extra'] = tuple(no_variant_attributes_price_extra)

        return res

    @api.depends('product_id')
    def _compute_no_variant_attribute_values(self):
        for line in self:
            if not line.product_id:
                line.product_no_variant_attribute_value_ids = False
                continue
            if not line.product_no_variant_attribute_value_ids:
                continue
            valid_values = line.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
            for ptav in line.product_no_variant_attribute_value_ids:
                if ptav._origin not in valid_values:
                    line.product_no_variant_attribute_value_ids -= ptav

    @api.onchange('planned_qty', 'cost','uom_id')
    def onchange_planned_qty(self):
        for line in self:
            if line.product_id:
                price = line.with_company(line.company_id)._get_display_price()
                if line.product_id:
                    if not line.cost:
                        if line.uom_id:
                            line.cost = price
                        else:
                            line.cost = line.product_id.uom_id._compute_price(line.product_id.standard_price, line.product_id.uom_id)

            price = line.planned_qty * line.cost
            actual_price = line.actual_qty * line.cost
            line.total_cost = price
            line.total_actual_cost = actual_price


class MrpBomLabourCost(models.Model):
    _name = "mrp.bom.labour.cost"
    _description = "MRP BOM LABOUR COST"
    
    
    
    def write(self, vals):
        return super().write(vals)

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if not self.product_id:
            return res
        self.uom_id = self.product_id.uom_id.id

    @api.onchange('planned_qty', 'cost')
    def onchange_labour_planned_qty(self):
        for line in self:
            price = line.planned_qty * line.cost
            actual_price = line.actual_qty * line.cost
            line.total_cost = price
            line.total_actual_cost = actual_price
            
            
   

    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id

    operation_id = fields.Many2one('mrp.routing.workcenter', string="Operation")
    product_id = fields.Many2one('product.template', string="Product")
    product_product_id = fields.Many2one('product.product', string="Product")
    planned_qty = fields.Float(string="Planned Hour",store=True)
    actual_qty = fields.Float(string="Actual Hour", default=0.0)
    uom_id = fields.Many2one('uom.uom', string="UOM")
    workcenter_id = fields.Many2one('mrp.workcenter', string="Workcenter")
    cost = fields.Float(string="Cost/Hour")
    total_cost = fields.Float(compute='onchange_labour_planned_qty', string="Total Cost")
    total_actual_cost = fields.Float(compute='onchange_labour_planned_qty', string="Total Actual Cost")
    mrp_bom_labour_id = fields.Many2one("mrp.bom", "Mrp Bom Labour")
    mrp_pro_labour_id = fields.Many2one("mrp.production", "Mrp Production Labour")
    mrp_wo_labour_id = fields.Many2one("mrp.workorder", "Mrp Workorder Labour")
    currency_id = fields.Many2one("res.currency", compute='get_currency_id', string="Currency")
    mrp_bom_line_id = fields.Many2one("mrp.bom.line", "Mrp Bom Line")



class MrpBomOverheadCost(models.Model):
    _name = "mrp.bom.overhead.cost"
    _description = "MRP BOM OVERHEAD COST"

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if not self.product_id:
            return res
        self.uom_id = self.product_id.uom_id.id

    @api.onchange('planned_qty', 'cost')
    def onchange_overhead_planned_qty(self):
        for line in self:
            price = line.planned_qty * line.cost
            actual_price = line.actual_qty * line.cost
            line.total_cost = price
            line.total_actual_cost = actual_price

    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id

    operation_id = fields.Many2one('mrp.routing.workcenter', string="Operation")
    product_id = fields.Many2one('product.template', string="Product")
    product_product_id = fields.Many2one('product.product', string="Product")
    planned_qty = fields.Float(string="Planned Hour", default=0.0)
    actual_qty = fields.Float(string="Actual Hour", default=0.0)
    uom_id = fields.Many2one('uom.uom', string="UOM")
    workcenter_id = fields.Many2one('mrp.workcenter', string="Workcenter")
    cost = fields.Float(string="Cost/Hour")
    total_cost = fields.Float(compute='onchange_overhead_planned_qty', string="Total Cost")
    total_actual_cost = fields.Float(compute='onchange_overhead_planned_qty', string="Total Actual Cost")
    mrp_bom_overhead_id = fields.Many2one("mrp.bom", "Mrp Bom Overhead")
    mrp_pro_overhead_id = fields.Many2one("mrp.production", "Mrp Production Overhead")
    mrp_wo_overhead_id = fields.Many2one("mrp.workorder", "Mrp Workorder Overhead")
    currency_id = fields.Many2one("res.currency", compute='get_currency_id', string="Currency")
    mrp_bom_line_id = fields.Many2one("mrp.bom.line", "Mrp Bom Line")


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string="Pricelist",
        compute='_compute_pricelist_id',
        store=True, readonly=False, precompute=True, check_company=True,
        tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="If you change the pricelist, only newly added lines will be affected.")
    current_user = fields.Many2one('res.users', 'Current User', default=lambda self: self.env.user.id)

    def _compute_pricelist_id(self):
        for order in self:
            if not order.current_user:
                order.pricelist_id = False
                continue
            order = order.with_company(order.company_id)
            order.pricelist_id = order.current_user.property_product_pricelist

    def copy(self, default=None):
        res = super().copy(default)

        for line in res.pro_labour_cost_ids:
            line.unlink()
        for line in res.pro_overhead_cost_ids:
            line.unlink()
        for line in res.pro_material_cost_ids:
            line.unlink()
        for labour in self.pro_labour_cost_ids:
            new_line = labour.copy()
            new_line.write({'mrp_pro_labour_id': res.id})
        for overhead in self.pro_overhead_cost_ids:
            new_line = overhead.copy()
            new_line.write({'mrp_pro_overhead_id': res.id})
        for material in self.pro_material_cost_ids:
            new_line = material.copy()
            new_line.write({'mrp_pro_material_id': res.id})

        return res
    
    @api.model_create_multi
    def create(self, vals_list):
        res = super(MrpProduction, self).create(vals_list)

        for record in res:
            list_of_material = []
            list_of_labour = []
            list_of_overhead = []
            bom = record.bom_id

            if bom:
                for labour in bom.bom_labour_cost_ids:
                    vals = {
                        'operation_id': labour.operation_id.id,
                        'product_id': labour.product_id.id,
                        'planned_qty': labour.planned_qty,
                        'uom_id': labour.uom_id.id,
                        'cost': labour.cost or False,
                        'mrp_pro_labour_id': record.id,
                    }
                    labour_res = self.env["mrp.bom.labour.cost"].create(vals)

                for overhead in bom.bom_overhead_cost_ids:
                    vals = {
                        'operation_id': overhead.operation_id.id,
                        'product_id': overhead.product_id.id,
                        'planned_qty': overhead.planned_qty,
                        'uom_id': overhead.uom_id.id,
                        'cost': overhead.cost or False,
                        'mrp_pro_overhead_id': record.id,
                    }
                    overhead_res = self.env["mrp.bom.overhead.cost"].create(vals)

                for material in record.move_raw_ids:
                    product_id = self.env['product.template'].search([('id', '=', material.product_id.product_tmpl_id.id)])
                    bom_materials = self.env['mrp.bom.material.cost'].search([
                        ('product_id', '=', product_id.id),
                        ('mrp_bom_material_id', '=', bom.id)
                    ])

                    for bom_material in bom_materials:
                        if bom_material:
                            vals = {
                                'product_id': product_id.id,
                                'planned_qty': material.product_uom_qty,
                                'uom_id': bom_material.uom_id.id,
                                'cost': bom_material.cost,
                                'operation_id': bom_material.operation_id.id,
                                'mrp_pro_material_id': record.id,
                            }
                            if record.product_qty <= 1:
                                self.env['mrp.bom.material.cost'].create(vals)

        return res

    @api.onchange('product_qty')
    def _onchange_qty(self):
        list1 = []
        for material in self.move_raw_ids:
            product_id = self.env['product.template'].search([('id', '=', material.product_id.product_tmpl_id.id)])

            bom_material = self.env['mrp.bom.material.cost'].search(
                [('product_id', '=', product_id.id), ('mrp_bom_material_id', '=', self.bom_id.id)], limit=1)
            if bom_material:
                list1.append([0, 0, {'product_id': product_id.id,
                                     'planned_qty': material.product_uom_qty,
                                     'uom_id': bom_material.uom_id.id,
                                     'cost': bom_material.cost,
                                     'operation_id': bom_material.operation_id.id,
                                     'mrp_pro_material_id': self.id,
                                    }])
        self.pro_material_cost_ids = [(6, 0, [])]
        self.write({'pro_material_cost_ids': list1})

    def _compute_total_cost(self):
        
        
        material_total = 0.0
        material_actual_total = 0.0

        labour_total = 0.0
        labour_actual_total = 0.0

        overhead_total = 0.0
        overhead_actual_total = 0.0

        for line in self.pro_material_cost_ids:
            material_total += line.total_cost
            material_actual_total += line.total_actual_cost

        for line in self.pro_labour_cost_ids:
            labour_total += line.total_cost
            labour_actual_total += line.total_actual_cost

        for line in self.pro_overhead_cost_ids:
            overhead_total += line.total_cost
            overhead_actual_total += line.total_actual_cost

        self.total_material_cost = material_total
        self.total_actual_material_cost = material_actual_total

        self.total_labour_cost = labour_total
        self.total_actual_labour_cost = labour_actual_total

        self.total_overhead_cost = overhead_total
        self.total_actual_overhead_cost = overhead_actual_total

    def _compute_total_all_cost(self):
        for mrp in self:
            total = 0.0
            actual_total = 0.0
            total = mrp.total_material_cost + mrp.total_labour_cost + mrp.total_overhead_cost
            actual_total = mrp.total_actual_material_cost + mrp.total_actual_labour_cost + mrp.total_actual_overhead_cost
            mrp.total_all_cost = total
            mrp.total_actual_all_cost = actual_total

    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id

    def _compute_total_product_cost(self):
        total = 0.0
        for line in self.finished_move_line_ids:
            if line.quantity != 0.0:
                total = self.total_actual_all_cost / self.product_qty
        self.product_unit_cost = total

    # def button_mark_done(self):
    #     for line in self.move_raw_ids:
    #         for mo in self.pro_material_cost_ids:
    #             if line.product_id.product_tmpl_id.id == mo.product_id.id:
    #                 if mo.actual_qty == 0.00:
    #                     mo.write({'actual_qty': line.quantity})

    #     res = super(MrpProduction, self).button_mark_done()
    #     return res
    
    
    def button_mark_done(self):
        res = super(MrpProduction, self).button_mark_done()

      
        for line in self.move_raw_ids:
            for mo in self.pro_material_cost_ids:
                if line.product_id.product_tmpl_id.id == mo.product_id.id:
                    if mo.actual_qty == 0.00:
                        mo.write({'actual_qty': line.quantity})

       
        for wo in self.workorder_ids:
            actual_hour = wo.duration / 60

            labour_lines = self.pro_labour_cost_ids.filtered(
                lambda l: l.operation_id.id == wo.operation_id.id
                and l.actual_qty == 0.0
            )
            if labour_lines:
                labour_lines.write({'actual_qty': actual_hour})
            else:
                self.pro_labour_cost_ids.filtered(
                    lambda l: l.actual_qty == 0.0
                ).write({'actual_qty': actual_hour})

            overhead_lines = self.pro_overhead_cost_ids.filtered(
                lambda l: l.operation_id.id == wo.operation_id.id
                and l.actual_qty == 0.0
            )
            if overhead_lines:
                overhead_lines.write({'actual_qty': actual_hour})
            else:
                self.pro_overhead_cost_ids.filtered(
                    lambda l: l.actual_qty == 0.0
                ).write({'actual_qty': actual_hour})

        
        if not self.workorder_ids:
            for labour in self.pro_labour_cost_ids.filtered(
                lambda l: l.actual_qty == 0.0
            ):
                labour.write({'actual_qty': labour.planned_qty})
            for overhead in self.pro_overhead_cost_ids.filtered(
                lambda l: l.actual_qty == 0.0
            ):
                overhead.write({'actual_qty': overhead.planned_qty})

        return res
    
    
    

    currency_id = fields.Many2one("res.currency", compute='get_currency_id', string="Currency")

    pro_material_cost_ids = fields.One2many("mrp.bom.material.cost", "mrp_pro_material_id", "Material Cost")
    pro_labour_cost_ids = fields.One2many("mrp.bom.labour.cost", "mrp_pro_labour_id", "Labour Cost")
    pro_overhead_cost_ids = fields.One2many("mrp.bom.overhead.cost", "mrp_pro_overhead_id", "Overhead Cost")
    pro_total_material_cost = fields.Float(string="Total Material Costt", default=0.0)

    total_material_cost = fields.Float(compute='_compute_total_cost', string="Total Material Cost", default=0.0)
    total_labour_cost = fields.Float(compute='_compute_total_cost', string="Total Labour Cost", default=0.0)
    total_overhead_cost = fields.Float(compute='_compute_total_cost', string="Total Overhead Cost", default=0.0)
    total_all_cost = fields.Float(compute='_compute_total_all_cost', string="Total Cost", default=0.0)

    total_actual_material_cost = fields.Float(compute='_compute_total_cost', string="Total Actual Material Cost",
                                              default=0.0)
    total_actual_labour_cost = fields.Float(compute='_compute_total_cost', string="Total Actual Labour Cost",
                                            default=0.0)
    total_actual_overhead_cost = fields.Float(compute='_compute_total_cost', string="Total Actual Overhead Cost",
                                              default=0.0)
    total_actual_all_cost = fields.Float(compute='_compute_total_all_cost', string="Total Actual Cost", default=0.0)

    product_unit_cost = fields.Float(compute='_compute_total_product_cost', string="Product Unit Cost", default=0.0)


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    
    # def button_finish(self):
    #     total_duration = sum(self.mapped('duration'))
    #     actual_hour = total_duration / 60
        
    #     for line in self:
    #         # Direct SQL update (faster for bulk operations)
    #         self.env.cr.execute("""
    #             UPDATE mrp_bom_labour_cost 
    #             SET actual_qty = %s 
    #             WHERE mrp_pro_labour_id = %s AND operation_id = %s
    #         """, (actual_hour, line.production_id.id, line.operation_id.id))
        
    #     return super(MrpWorkorder, self).button_finish()
    
    
    def button_finish(self):
        res = super(MrpWorkorder, self).button_finish()

        
        for line in self:
            actual_hour = line.duration / 60

            labour = self.env['mrp.bom.labour.cost'].search([
                ('mrp_pro_labour_id', '=', line.production_id.id),
                ('operation_id', '=', line.operation_id.id),
                ('actual_qty', '=', 0.0),
            ])
            if labour:
                labour.write({'actual_qty': actual_hour})
            else:
                line.production_id.pro_labour_cost_ids.filtered(
                    lambda l: l.actual_qty == 0.0
                ).write({'actual_qty': actual_hour})

            overhead = self.env['mrp.bom.overhead.cost'].search([
                ('mrp_pro_overhead_id', '=', line.production_id.id),
                ('operation_id', '=', line.operation_id.id),
                ('actual_qty', '=', 0.0),
            ])
            if overhead:
                overhead.write({'actual_qty': actual_hour})
            else:
                line.production_id.pro_overhead_cost_ids.filtered(
                    lambda l: l.actual_qty == 0.0
                ).write({'actual_qty': actual_hour})

        return res
    
    

    def _compute_total_cost(self):
        material_total = 0.0
        material_actual_total = 0.0
        labour_total = 0.0
        labour_actual_total = 0.0
        overhead_total = 0.0
        overhead_actual_total = 0.0
        for order in self:
            for line in order.wo_material_cost_ids:
                material_total += line.total_cost
                material_actual_total += line.total_actual_cost
            order.total_material_cost = material_total
            order.total_actual_material_cost = material_actual_total
            for line in order.wo_labour_cost_ids:
                labour_total += line.total_cost
                labour_actual_total += line.total_actual_cost
            order.total_labour_cost = labour_total
            order.total_actual_labour_cost = labour_actual_total
            for line in order.wo_overhead_cost_ids:
                overhead_total += line.total_cost
                overhead_actual_total += line.total_actual_cost
            order.total_overhead_cost = overhead_total
            order.total_actual_overhead_cost = overhead_actual_total

    def _compute_total_all_cost(self):
        total = 0.0
        actual_total = 0.0
        for line in self:
            total = line.total_material_cost + line.total_labour_cost + line.total_overhead_cost
            actual_total = line.total_actual_material_cost + line.total_actual_labour_cost + line.total_actual_overhead_cost
            line.total_all_cost = total
            line.total_actual_all_cost = actual_total

    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id

    currency_id = fields.Many2one("res.currency", compute='get_currency_id', string="Currency")
    wo_material_cost_ids = fields.One2many("mrp.bom.material.cost", "mrp_wo_material_id", "Material Cost")
    wo_labour_cost_ids = fields.One2many("mrp.bom.labour.cost", "mrp_wo_labour_id", "Labour Cost")
    wo_overhead_cost_ids = fields.One2many("mrp.bom.overhead.cost", "mrp_wo_overhead_id", "Overhead Cost")
    actual_hour_wo = fields.Float(string="Actual Hour")
    total_material_cost = fields.Float(compute='_compute_total_cost', string="Total Material Cost", default=0.0)
    total_labour_cost = fields.Float(compute='_compute_total_cost', string="Total Labour Cost", default=0.0)
    total_overhead_cost = fields.Float(compute='_compute_total_cost', string="Total Overhead Cost", default=0.0)
    total_all_cost = fields.Float(compute='_compute_total_all_cost', string="Total Cost", default=0.0)
    total_actual_material_cost = fields.Float(compute='_compute_total_cost', string="Total Actual Material Cost",
                                              default=0.0)
    total_actual_labour_cost = fields.Float(compute='_compute_total_cost', string="Total Actual Labour Cost",
                                            default=0.0)
    total_actual_overhead_cost = fields.Float(compute='_compute_total_cost', string="Total Actual Overhead Cost",
                                              default=0.0)
    total_actual_all_cost = fields.Float(compute='_compute_total_all_cost', string="Total Actual Cost", default=0.0)

    product_unit_cost = fields.Float(string="Product Unit Cost", default=0.0)


class ChangeProductionQty(models.TransientModel):
    _inherit = 'change.production.qty'

    def change_prod_qty(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for wizard in self:
            production = wizard.mo_id
            produced = sum(
                production.move_finished_ids.filtered(lambda m: m.product_id == production.product_id).mapped(
                    'quantity'))
            if wizard.product_qty < produced:
                format_qty = '%.{precision}f'.format(precision=precision)
                raise UserError(_(
                    "You have already processed %(quantity)s. Please input a quantity higher than %(minimum)s ",
                    quantity=format_qty % produced,
                    minimum=format_qty % produced
                ))
            for material in production.pro_material_cost_ids:
                for bom in production.bom_id.bom_line_ids:
                    if material.product_id.id == bom.product_id.id:
                        material.write({'planned_qty': wizard.product_qty * bom.product_qty,
                                        'actual_qty': wizard.product_qty * bom.product_qty})
            for labour in production.pro_labour_cost_ids:
                for bom in production.bom_id.bom_labour_cost_ids:
                    if labour.product_id.id == bom.product_id.id:
                        labour.write({'planned_qty': wizard.product_qty * bom.planned_qty,
                                      'actual_qty': wizard.product_qty * bom.planned_qty})
            for overhead in production.pro_overhead_cost_ids:
                for bom in production.bom_id.bom_overhead_cost_ids:
                    if overhead.product_id.id == bom.product_id.id:
                        overhead.write({'planned_qty': wizard.product_qty * bom.planned_qty,
                                        'actual_qty': wizard.product_qty * bom.planned_qty})

            old_production_qty = production.product_qty
            new_production_qty = wizard.product_qty
            done_moves = production.move_finished_ids.filtered(lambda x: x.state == 'done' and x.product_id == production.product_id)
            qty_produced = production.product_id.uom_id._compute_quantity(sum(done_moves.mapped('product_qty')), production.product_uom_id)
            
            factor = (new_production_qty - qty_produced) / (old_production_qty - qty_produced)
            update_info = production._update_raw_moves(factor)
            documents = {}
            for move, old_qty, new_qty in update_info:
                iterate_key = production._get_document_iterate_key(move)
                if iterate_key:
                    document = self.env['stock.picking']._log_activity_get_documents({move: (new_qty, old_qty)}, iterate_key, 'UP')
                    for key, value in document.items():
                        if documents.get(key):
                            documents[key] += [value]
                        else:
                            documents[key] = [value]
            production._log_manufacture_exception(documents)
            finished_moves_modification = self._update_finished_moves(production, new_production_qty - qty_produced, old_production_qty - qty_produced)
            if finished_moves_modification:
                production._log_downside_manufactured_quantity(finished_moves_modification)
            production.write({'product_qty': new_production_qty})
            
            if not float_is_zero(production.qty_producing, precision_rounding=production.product_uom_id.rounding) and\
               not production.workorder_ids:
                production.qty_producing = new_production_qty
                production._set_qty_producing()

            for wo in production.workorder_ids:
                operation = wo.operation_id
                wo.duration_expected = wo._get_duration_expected(ratio=new_production_qty / old_production_qty)
                quantity = wo.qty_production - wo.qty_produced
                if production.product_id.tracking == 'serial':
                    quantity = 1.0 if not float_is_zero(quantity, precision_digits=precision) else 0.0
                else:
                    quantity = quantity if (quantity > 0 and not float_is_zero(quantity, precision_digits=precision)) else 0
                wo._update_qty_producing(quantity)
                if wo.qty_produced < wo.qty_production and wo.state == 'done':
                    wo.state = 'progress'
                if wo.qty_produced == wo.qty_production and wo.state == 'progress':
                    wo.state = 'done'
                # TODO: following could be put in a function as it is similar as code in _workorders_create
                # TODO: only needed when creating new moves
                moves_raw = production.move_raw_ids.filtered(lambda move: move.operation_id == operation and move.state not in ('done', 'cancel'))
                if wo == production.workorder_ids[-1]:
                    moves_raw |= production.move_raw_ids.filtered(lambda move: not move.operation_id)
                moves_finished = production.move_finished_ids.filtered(lambda move: move.operation_id == operation) #TODO: code does nothing, unless maybe by_products?
                moves_raw.mapped('move_line_ids').write({'workorder_id': wo.id})
                (moves_finished + moves_raw).write({'workorder_id': wo.id})
        self.mo_id.filtered(lambda mo: mo.state in ['confirmed', 'progress']).move_raw_ids._trigger_scheduler()
        return {}


class ReportBomStructure(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'

    @api.model
    def _get_component_data(self, parent_bom, parent_product, warehouse, bom_line, line_quantity, level, index, product_info, ignore_stock=False):
        company = parent_bom.company_id or self.env.company
        price = bom_line.product_id.uom_id._compute_price(bom_line.product_id.with_company(company).standard_price,
                                                          bom_line.product_uom_id) * line_quantity
        rounded_price = company.currency_id.round(price)
        if parent_bom.bom_material_cost_ids:
            get_ids = self.env['mrp.bom.material.cost'].search([('product_id','=',bom_line.product_id.product_tmpl_id.id),('mrp_bom_material_id','=',parent_bom.id)])
            if get_ids:
                rounded_price_cost = company.currency_id.round(get_ids.cost)
            else:
                rounded_price_cost = rounded_price
        else:
            rounded_price_cost = rounded_price

        key = bom_line.product_id.id
        bom_key = parent_bom.id
        self._update_product_info(bom_line.product_id, bom_key, product_info, warehouse, line_quantity, bom=False, parent_bom=parent_bom, parent_product=parent_product)
        route_info = product_info[key].get(bom_key, {})

        quantities_info = {}
        if not ignore_stock:
            quantities_info = self._get_quantities_info(bom_line.product_id, bom_line.product_uom_id, parent_bom,
                                                        product_info)
        availabilities = self._get_availabilities(bom_line.product_id, line_quantity, product_info, bom_key,
                                                  quantities_info, level, ignore_stock, bom_line=bom_line)

        has_attachments = False
        if not self.env.context.get('minimized', False):
            has_attachments = self.env['product.document'].search_count(
                ['&', ('attached_on_mrp', '=', 'bom'), '|', '&', ('res_model', '=', 'product.product'),
                 ('res_id', '=', bom_line.product_id.id),
                 '&', ('res_model', '=', 'product.template'),
                 ('res_id', '=', bom_line.product_id.product_tmpl_id.id)]) > 0

        return {
            'type': 'component',
            'index': index,
            'bom_id': False,
            'product': bom_line.product_id,
            'product_id': bom_line.product_id.id,
            'product_template_id': bom_line.product_tmpl_id.id,
            'link_id': bom_line.product_id.id if bom_line.product_id.product_variant_count > 1 else bom_line.product_id.product_tmpl_id.id,
            'link_model': 'product.product' if bom_line.product_id.product_variant_count > 1 else 'product.template',
            'name': bom_line.product_id.display_name,
            'code': '',
            'currency': company.currency_id,
            'currency_id': company.currency_id.id,
            'is_storable': bom_line.product_id.is_storable,
            'quantity': line_quantity,
            'quantity_available': quantities_info.get('free_qty', 0),
            'quantity_on_hand': quantities_info.get('on_hand_qty', 0),
            'quantity_forecasted': quantities_info.get('forecasted_qty', 0),
            'free_to_manufacture_qty': quantities_info.get('free_to_manufacture_qty', 0),
            'base_bom_line_qty': bom_line.product_qty,
            'uom': bom_line.product_uom_id,
            'uom_name': bom_line.product_uom_id.name,
            'bom_cost': rounded_price,
            'route_type': route_info.get('route_type', ''),
            'route_name': route_info.get('route_name', ''),
            'route_detail': route_info.get('route_detail', ''),
            'route_alert': route_info.get('route_alert', False),
            'lead_time': route_info.get('lead_time', False),
            'manufacture_delay': route_info.get('manufacture_delay', False),
            'stock_avail_state': availabilities['stock_avail_state'],
            'resupply_avail_delay': availabilities['resupply_avail_delay'],
            'availability_display': availabilities['availability_display'],
            'availability_state': availabilities['availability_state'],
            'availability_delay': availabilities['availability_delay'],
            'parent_id': parent_bom.id,
            'level': level or 0,
            'has_attachments': has_attachments,
        }
