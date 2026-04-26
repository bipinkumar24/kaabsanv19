from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ExpenseTransferWizardData(models.TransientModel):
    _name = 'expense.transfer.wizard.data'
    _description = 'Expense Transfer Wizard'

    def get_expense_operation_type(self):
        expense_operation_type_id = self.env['stock.picking.type'].search([('sequence_code', '=', 'EXP')], limit=1)
        return [('id','in', expense_operation_type_id.ids)]

    picking_type_id = fields.Many2one('stock.picking.type', string="Operation Type", domain=get_expense_operation_type)
    location_id = fields.Many2one('stock.location', string='Source Location')
    location_dest_id = fields.Many2one('stock.location', string='Destination Location')
    employee_id = fields.Many2one('hr.employee', string="Employee")
    property_stock_account_output_categ_id = fields.Many2one(
        'account.account', 'Stock Output Account', company_dependent=True,
        domain="[('company_id', '=', allowed_company_ids[0]), ('deprecated', '=', False)]", check_company=True,
        help="""When doing automated inventory valuation, counterpart journal items for all outgoing stock moves will be posted in this account,
                        unless there is a specific valuation account set on the destination location. This is the default value for all products in this category.
                        It can also directly be set on each product.""")
    type_data = fields.Selection([('computer', 'Equipment'),
                                  ('car', 'Car'),
                                  ('other', 'Other')],
                                  default='computer',
                                  string='Type')
    fleet_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    odometer = fields.Float(string="Last Odometer", related="fleet_id.odometer")
    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    picking_type_code = fields.Selection(
        related='picking_type_id.code',
        readonly=True)

    def action_create_expense_transfer(self):
        expense_operation_type_id = self.env['stock.picking.type'].search([('sequence_code', '=', 'EXP')])
        if not expense_operation_type_id:
            raise ValidationError(_('Please Configure Expense Transfer Picking Type'))
        request_id = self.env['purchase.request'].browse(self.env.context.get('active_id'))
        line_ids = request_id.line_ids.filtered(lambda x:x.expense_create)
        for line in line_ids:
            line.write({'state_creation': 'expense'})
        Location = self.env['stock.location']
        customer_loc = Location.search([('usage', '=', 'customer')], limit=1)
        pickingA_out = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': customer_loc.id,
            'employee_id': self.employee_id.id,
            'property_stock_account_output_categ_id': self.property_stock_account_output_categ_id.id,
            'type_data': self.type_data,
            'fleet_id': self.fleet_id.id,
            'odometer': self.odometer,
            'equipment_id': self.equipment_id.id,
            'is_expense': True,
            'purchase_request_id': request_id.id
            })
        for line in line_ids:
            line.expense_transfer_id = pickingA_out.id
            self.env['stock.move'].create({
            'name': 'Picking A move',
            'product_id': line.product_id.id,
            'product_uom_qty': line.request_qty,
            'product_uom': line.product_id.uom_id.id,
            'picking_id': pickingA_out.id,
            'location_id': self.location_id.id,
            'location_dest_id': customer_loc.id})
