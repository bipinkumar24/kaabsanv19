# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    def _get_default_scrap_location_id(self):
        company_id = self.env.context.get('default_company_id') or self.env.company.id
        if self.is_fual_expense:
            return self.env['stock.location'].search(
                [('is_fual_expense', '=', True), ('company_id', 'in', [company_id, False])], limit=1).id
        return self.env['stock.location'].search(
            [('usage', '=', 'inventory'), ('company_id', 'in', [company_id, False])], limit=1).id

    def action_validate_data(self):
        for scraps in self:
            domain = [('id', 'in', (scraps.stock_move_ids + scraps.move_id).stock_valuation_layer_ids.ids)]
            valuation_ids = self.env['stock.valuation.layer'].search(domain)
            for valuation in valuation_ids:
                if valuation.account_move_id:
                    if valuation.account_move_id.state != 'posted':
                        valuation.account_move_id._post()
            scraps.sudo().write({'state': 'validate'})

    def action_unpost_entery(self):
        for scraps in self:
            domain = [('id', 'in', (scraps.stock_move_ids + scraps.move_id).stock_valuation_layer_ids.ids)]
            valuation_ids = self.env['stock.valuation.layer'].search(domain)
            for valuation in valuation_ids:
                if valuation.account_move_id:
                    if valuation.account_move_id.state == 'posted':
                        valuation.account_move_id.button_draft()
            scraps.sudo().write({'state': 'done'})

    def doamin_location_scrap(self):
        if self.is_fual_expense:
            location_ids = self.env['stock.location'].search([('is_fual_expense', '=', True)])
            return [('id', 'in', location_ids.ids)]
        else:
            location_ids = self.env['stock.location'].search([('usage', '=', 'inventory')])
            return [('id', 'in', location_ids.ids)]

    is_fual_expense = fields.Boolean(string="Is Fual Expense Location")
    scrap_location_id = fields.Many2one(
        'stock.location', 'Scrap Location', domain=doamin_location_scrap, required=False,
        default=_get_default_scrap_location_id, check_company=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('procurement_manager', 'Procurement Manager'),
        ('finance', 'Store Keeper Approval'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
        ('validate', 'Validate')
    ],
        string='Status', default="draft", readonly=True, tracking=True)
    hide_validate = fields.Boolean(string="Validate Boolean")

    employee_id = fields.Many2one('hr.employee', 'Employee')
    analytic_id = fields.Many2one('account.analytic.account', string="Analytic Accounts")
    request_uid = fields.Many2one(
        comodel_name='res.users',
        string='Requester'
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department'
    )
    type_data = fields.Selection([('computer', 'Equipment'),
                                  ('car', 'Car'), ('other', 'Other')],
                                 default='computer',
                                 string='Type')
    curreent_odoo_meter = fields.Float(string="Current Odometer")
    fleet_id = fields.Many2one('fleet.vehicle', string="Vehicle", required=False)
    odometer = fields.Float(string="Last Odometer", compute="_compute_odometer", store=True)
    consumption = fields.Float(string="Distance Traveled", compute="_compute_consumption", store=True)
    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    effective_date = fields.Date('Effective Date')
    average_fuel = fields.Float('Average Fuel Consumed', compute='compute_average_fuel_consumed', store=True)
    is_mutiline = fields.Boolean(string="Multi Location")
    scrap_line_ids = fields.One2many('stock.scrap.line', 'scrap_id', string="Scrap Line")
    stock_move_ids = fields.Many2many('stock.move', string="Stock Move", copy=False)

    # @api.constrains('curreent_odoo_meter', 'odometer')
    # def _check_odometer(self):
    #     for scrap in self:
    #         if scrap.curreent_odoo_meter <= scrap.odometer:
    #             raise ValidationError(_("Please make sure the current odometer is greater than the last odometer."))

    @api.depends('fleet_id.odometer', 'fleet_id')
    def _compute_odometer(self):
        for fleet in self:
            fleet.odometer = fleet.fleet_id.odometer

    @api.constrains('scrap_line_ids.qty', 'scrap_line_ids', 'is_mutiline')
    def _total_qty_scrap(self):
        for rec in self:
            if rec.is_mutiline:
                total_qty = 0
                for line in self.scrap_line_ids:
                    total_qty += round(line.qty, 2)
                if total_qty != round(rec.scrap_qty, 2):
                    raise ValidationError(_("Total Qty Should not be greater/less then Actual Qty"))

    @api.depends('fleet_id', 'curreent_odoo_meter')
    def compute_average_fuel_consumed(self):
        for rec in self:
            last_rec_id = self.env['stock.scrap'].search([('fleet_id', '=', rec.fleet_id.id)])
            if last_rec_id and len(last_rec_id) > 1:
                last_rec_id = last_rec_id[1]
                if rec.consumption and last_rec_id.scrap_qty:
                    rec.average_fuel = last_rec_id.scrap_qty / rec.consumption
                else:
                    rec.average_fuel = 0
            else:
                rec.average_fuel = 0

    def action_get_stock_move_lines(self):
        if self.is_mutiline:
            action = self.env['ir.actions.act_window']._for_xml_id('stock.stock_move_action')
            action['domain'] = [('id', 'in', self.stock_move_ids.ids)]
            return action
        else:
            action = self.env['ir.actions.act_window']._for_xml_id('stock.stock_move_action')
            action['domain'] = [('id', '=', self.move_id.id)]
            return action

    def _prepare_move_values(self):
        self.ensure_one()
        return {
            'origin': self.origin or self.picking_id.name or self.name,
            'company_id': self.company_id.id,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'state': 'draft',
            'product_uom_qty': self.scrap_qty,
            'location_id': self.location_id.id,
            'scrapped': True,
            'location_dest_id': self.scrap_location_id.id,
            'move_line_ids': [(0, 0, {'product_id': self.product_id.id,
                                      'product_uom_id': self.product_uom_id.id,
                                      'quantity': self.scrap_qty,
                                      'picked': True,
                                      'location_id': self.location_id.id,
                                      'location_dest_id': self.scrap_location_id.id,
                                      'package_id': self.package_id.id,
                                      'owner_id': self.owner_id.id,
                                      'lot_id': self.lot_id.id, })],
            #             'restrict_partner_id': self.owner_id.id,
            'picking_id': self.picking_id.id
        }

    def _new_mutiline_picking(self, source, destination, qty):
        self.ensure_one()

        return {
            'origin': self.origin or self.picking_id.name or self.name,
            'company_id': self.company_id.id,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'state': 'draft',
            'product_uom_qty': qty,
            'location_id': source.id,
            'scrapped': True,
            'location_dest_id': destination.id,
            'move_line_ids': [(0, 0, {'product_id': self.product_id.id,
                                      'product_uom_id': self.product_uom_id.id,
                                      'quantity': qty,
                                      'picked': True,
                                      'location_id': self.location_id.id,
                                      'location_dest_id': self.scrap_location_id.id,
                                      'owner_id': self.owner_id.id,
                                      })],
            #             'restrict_partner_id': self.owner_id.id,
            # 'picking_id': self.picking_id.id
        }

    def do_scrap(self):
        self._check_company()
        for scrap in self:
            scrap.name = self.env['ir.sequence'].next_by_code('stock.scrap') or _('New')
            if scrap.is_mutiline:
                for line in scrap.scrap_line_ids:
                    move = self.env['stock.move'].create({
                        'date': self.create_date,
                        'product_id': self.product_id.id,
                        'product_uom_qty': line.qty,
                        'product_uom': self.product_uom_id.id,
                        'location_dest_id': line.scrap_location_id.id,
                        'location_id': line.scrap_id.location_id.id,
                        'company_id': self.company_id.id,
                    })
                    move._action_confirm()
                    move._action_assign()
                    line.write({'move_id': move.id})
                    for move_line in move.move_line_ids:
                        move_line.quantity = line.qty
                        move_line.picked = True
                    move.with_context(is_scrap=True)._action_done()
                    scrap.write({'state': 'done'})
                    scrap.write({'stock_move_ids': [(4, move.id, 0)]})
            else:
                move = self.env['stock.move'].create(scrap._prepare_move_values())
                # master: replace context by cancel_backorder
                move.with_context(is_scrap=True)._action_done()
                scrap.write({'move_id': move.id, 'state': 'done'})
                scrap.date_done = fields.Datetime.now()
        return True

    def all_ready_do_scrap(self):
        for scrap in self:
            scrap.move_id._do_unreserve()
            scrap.move_id._action_confirm()
            scrap.move_id._action_assign()
            scrap.move_id.move_line_ids.quantity = scrap.scrap_qty
            scrap.move_id.move_line_ids.picked = True
            scrap.move_id._action_done()
            scrap.write({'state': 'done'})
            scrap.date_done = fields.Datetime.now()
        return True

    def action_confirm_assign_muti_stock(self, qty, move_id):
        for scrap in self:
            move_id._do_unreserve()
            move_id._action_confirm()
            move_id._action_assign()
            move_id.move_line_ids.quantity = qty
            move_id.move_line_ids.picked = True
            move_id._action_done()
        return True

    def all_ready_do_scrap_muti(self):
        for scrap in self:
            scrap.write({'state': 'done'})
            scrap.date_done = fields.Datetime.now()
        return True

    @api.depends('odometer', 'curreent_odoo_meter', 'fleet_id')
    def _compute_consumption(self):
        for rec in self:
            print("*****************************YYYYYYYYYYYYYYYYYYYYYYYYYYYY")
            rec.consumption = rec.curreent_odoo_meter - rec.odometer

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if self._context.get('default_is_fual_expense'):
            for node in arch.xpath("//field[@name='scrap_location_id']"):
                node.set('string', _('Fuel Expense Location'))
        return arch, view

    @api.onchange('is_fual_expense')
    def onchange_based_destination(self):
        if self.is_fual_expense:
            location_ids = self.env['stock.location'].search([('is_fual_expense', '=', True)])
            self.scrap_location_id = False
            if self.state == 'draft':
                self.hide_validate = True
            domain = [('id', 'in', location_ids.ids)]
            return {'domain': {'scrap_location_id': domain}}

    def submit_procument_manager(self):
        self.state = 'procurement_manager'
        self.hide_validate = False

    def submit_finance_approval(self):
        self.state = 'finance'

    def action_reject(self):
        self.state = 'cancel'

    def action_validate(self):
        self.ensure_one()

        if self.fleet_id:
            finger_templates = self.env['fleet.vehicle.odometer'].create({
                'date': fields.Date.today(),
                'vehicle_id': self.fleet_id.id,
                'value': self.consumption,
                'stock_scrap_id': self.id,
            })

        if not self.product_id.is_storable:
            return self.do_scrap()
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        available_qty = sum(self.env['stock.quant']._gather(self.product_id,
                                                            self.location_id,
                                                            self.lot_id,
                                                            self.package_id,
                                                            self.owner_id,
                                                            strict=True).mapped('quantity'))
        scrap_qty = self.product_uom_id._compute_quantity(self.scrap_qty, self.product_id.uom_id)
        if float_compare(available_qty, scrap_qty, precision_digits=precision) >= 0 and not self.move_id and not self.stock_move_ids:
            print("IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII")
            return self.do_scrap()
        elif self.move_id or self.stock_move_ids:
            if self.move_id:
                print("ssssssssssss")
                self.move_id.sudo().write({'product_uom_qty': self.scrap_qty})
                print(self.move_id.product_uom_qty, "product_uom_qtysqty")
                self.move_id.mapped('move_line_ids').sudo().write({'product_uom_qty': self.scrap_qty})
                amount = self.move_id.valuation_unit_price * self.move_id.product_uom_qty
                for account_move_id in self.move_id.account_move_ids:
                    for line in account_move_id.line_ids:
                        if line.credit > 0:
                            line.with_context(check_move_validity=False).write({'credit': amount})
                        if line.debit > 0:
                            line.with_context(check_move_validity=False).write({'debit': amount})
                return self.all_ready_do_scrap()
            if self.stock_move_ids:
                for scrap_line in self.scrap_line_ids:
                    scrap_line.move_id.sudo().write({'product_uom_qty': scrap_line.qty})
                    scrap_line.move_id.mapped('move_line_ids').sudo().write({'product_uom_qty': scrap_line.qty})
                    amount = scrap_line.move_id.valuation_unit_price * scrap_line.move_id.product_uom_qty
                    for account_move_id in scrap_line.move_id.account_move_ids:
                        for line in account_move_id.line_ids:
                            if line.credit > 0:
                                line.with_context(check_move_validity=False).write({'credit': amount})
                            if line.debit > 0:
                                line.with_context(check_move_validity=False).write({'debit': amount})
                    self.action_confirm_assign_muti_stock(scrap_line.qty, scrap_line.move_id)
                return self.all_ready_do_scrap_muti()
        else:
            print("EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE")
            ctx = dict(self.env.context)
            ctx.update({
                'default_product_id': self.product_id.id,
                'default_location_id': self.location_id.id,
                'default_scrap_id': self.id,
                'default_quantity': scrap_qty,
                'default_product_uom_name': self.product_id.uom_name
            })
            return {
                'name': self.product_id.display_name + _(': Insufficient Quantity To Scrap'),
                'view_mode': 'form',
                'res_model': 'stock.warn.insufficient.qty.scrap',
                'view_id': self.env.ref('stock.stock_warn_insufficient_qty_scrap_form_view').id,
                'type': 'ir.actions.act_window',
                'context': ctx,
                'target': 'new'
            }

    def write(self, values):
        if 'state' in values:
            if values.get('state') != 'done':
                odometer_id = self.env['fleet.vehicle.odometer'].search([('stock_scrap_id', '=', self.id)])
                if odometer_id:
                    odometer_id.with_context(delete_from_write=True).unlink()
        user = super(StockScrap, self).write(values)
        return user

    def action_update_odo_meter(self):
        vehicle_id = False
        for order in self:
            vehicle_id = order.fleet_id
        scrap_ids = self.env['stock.scrap'].search([('vehicle_id', '=', vehicle_id.id)], order='date_done asc')
        for scrap in scrap_ids:
            print(scrap_ids, "sdssssssssss")
        # for order in self:
        #     print(order, "ordersssssssssssssss")

class StockScrapOdometer(models.Model):
    _inherit = 'fleet.vehicle.odometer'

    stock_scrap_id = fields.Many2one('stock.scrap', string='Fuel Expense')

    def unlink(self):
        # Skip validation if context key 'is_delete' is True
        if not self.env.context.get('is_delete', False):
            if not self.env.context.get('delete_from_write', False) and self.stock_scrap_id:
                raise UserError('You cannot delete an odometer entry linked with a fuel expense!')
        
        return super(StockScrapOdometer, self).unlink()

class StockScrapLine(models.Model):
    _name = "stock.scrap.line"
    _description = "Stock Scrap Line"

    def _get_default_scrap_location_id(self):
        company_id = self.env.context.get('default_company_id') or self.env.company.id
        return self.env['stock.location'].search(
            [('usage', '=', 'inventory'), ('company_id', 'in', [company_id, False])], limit=1).id

    def _get_default_location_id(self):
        company_id = self.env.context.get('default_company_id') or self.env.company.id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        return None

    scrap_id = fields.Many2one('stock.scrap', string="Scrap")
    product_id = fields.Many2one('product.product', string="Product", related="scrap_id.product_id", store=True)
    qty = fields.Float(string="Qty")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    location_id = fields.Many2one(
        'stock.location', 'Source Location',
        domain="[('usage', '=', 'internal'), ('company_id', 'in', [company_id, False])]",
        required=True, default=_get_default_location_id, check_company=True)
    scrap_location_id = fields.Many2one(
        'stock.location', 'Fuel Expense Location', default=_get_default_scrap_location_id,
        domain="[('is_fual_expense', '=', True), ('company_id', 'in', [company_id, False])]", required=True,
        check_company=True)
    move_id = fields.Many2one('stock.move', string="Stock Move")

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    def action_update_odometers(self):
        odometer_ids = self.env['fleet.vehicle.odometer'].search([('vehicle_id', '=', self.id)])
        oldest_odometer = False
        if odometer_ids:
            # Sort by create_date ascending (oldest first)
            oldest_odometer = odometer_ids.sorted('create_date')[0]

            # Delete all except the oldest
            odometer_ids.with_context(is_delete=True).unlink()

        expense_ids = self.env['stock.scrap'].search([('fleet_id', '=', self.id), ('is_fual_expense', '=', True), ('state', 'in', ['done', 'validate'])])
        if expense_ids:
            sorted_expense_id = expense_ids.sorted('create_date')[0]
            sorted_expense_id.write({'odometer': 0})
            sorted_expense_id._compute_consumption()
            odometer_id = self.env['fleet.vehicle.odometer'].create({
                                            'date': sorted_expense_id.create_date.date(),
                                            'vehicle_id': sorted_expense_id.fleet_id.id,
                                            'value': sorted_expense_id.consumption,
                                            'stock_scrap_id': sorted_expense_id.id,
                                        })
            new_expense_ids = expense_ids - sorted_expense_id
            aseding_expense_ids = new_expense_ids.sorted('create_date')
            for expense in aseding_expense_ids:
                total_last_exepense = self.env['fleet.vehicle.odometer'].search([('vehicle_id', '=', expense.fleet_id.id)])
                total_last = sum(total_last_exepense.mapped('value'))
                expense.write({'odometer': total_last})
                expense._compute_consumption()
                consumption = expense.curreent_odoo_meter - total_last
                if consumption < 0 :
                    expense.write({'curreent_odoo_meter': total_last})
                    continue
                odometer_id = self.env['fleet.vehicle.odometer'].create({
                                    'date': expense.create_date.date(),
                                    'vehicle_id': expense.fleet_id.id,
                                    'value': consumption,
                                    'stock_scrap_id': expense.id,
                                })
        if not expense_ids and oldest_odometer:
            oldest_odometer.unlink()
