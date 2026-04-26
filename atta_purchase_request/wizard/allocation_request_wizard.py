from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AllocationRequestWizard(models.TransientModel):
    _name = 'allcation.request.wizard'
    _description = 'Allocation Request Wizard'

    subject = fields.Char(string="Subject")
    department_id = fields.Many2one('hr.department', string="Department", readonly=True)
    category_id = fields.Many2one('maintenance.equipment.category' , string='Category')
    equipment_id = fields.Many2one('maintenance.equipment' , string='Equipment')
    warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Warehouse",
        readonly=False,
        ondelete="cascade",
        required=True,
    )
    location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Sources",
        readonly=False,
        ondelete="cascade",
        required=True,
    )
    destination_id = fields.Many2one(
        comodel_name="stock.location",
        string="Destination",
        readonly=False,
        ondelete="cascade",
        required=True,
    )

    def action_allocation_request(self):
        request_id = self.env['purchase.request'].browse(self.env.context.get('active_id'))
        line_ids = request_id.line_ids.filtered(lambda x: x.allocation_create)
        for line in line_ids:

            if line.rfq_create:
                if line.order_line_ids:
                    employee_id = self.env['hr.employee'].search([('user_id', '=', self.create_uid.id)])
                    allocation_request_id = self.env['allcation.request'].create({'subject': self.subject,
                                                                              'product_id': line.product_id.id,
                                                                              'warehouse_id': self.warehouse_id.id,
                                                                              'sources_id': self.location_id.id,
                                                                              'destination_id': self.destination_id.id,
                                                                              'assing_to': employee_id.id,
                                                                              'purchase_request_id': request_id.id})
            if not line.rfq_create:
                employee_id = self.env['hr.employee'].search([('user_id', '=', self.create_uid.id)])
                allocation_request_id = self.env['allcation.request'].create({'subject': self.subject,
                                                                              'product_id': line.product_id.id,
                                                                              'warehouse_id': self.warehouse_id.id,
                                                                              'sources_id': self.location_id.id,
                                                                              'destination_id': self.destination_id.id,
                                                                              'assing_to': employee_id.id,
                                                                              'purchase_request_id': request_id.id})

    @api.model
    def default_get(self, fields_list):
        rslt = super(AllocationRequestWizard, self).default_get(fields_list)
        request_id = self.env['purchase.request'].browse(self.env.context.get('active_id'))
        rslt['department_id'] = request_id.department_id.id
        return rslt
