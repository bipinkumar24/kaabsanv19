from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ExpenseTransfer(models.Model):
    _inherit = 'stock.picking'

    purchase_request_line_id = fields.Many2one('purchase.request.line', string='Purchase Request Line')
    request_uid = fields.Many2one(
        comodel_name='res.users',
        string='Requester',
        readonly=True,
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department',
        readonly=True,
    )
    purchase_request_id = fields.Many2one('purchase.request', string="Purchase Request")
    type_data = fields.Selection([('computer', 'Equipment'),
                                  ('car', 'Car'),
                                  ('other', 'Other')],
                                  string='Type')
    vehicle_reg_number = fields.Char('Car Plate Number')
    vehicle_driver = fields.Char('Delivery Driver')
    fleet_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    odometer = fields.Float(string="Last Odometer", related="fleet_id.odometer")
    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
