# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    def _get_default_scrap_location_id(self):
        company_id = self.env.context.get('default_company_id') or self.env.company.id
        if self.is_fual_expense:
            return self.env['stock.location'].search([('is_fual_expense', '=', True), ('company_id', 'in', [company_id, False])], limit=1).id
        # return self.env['stock.location'].search([('scrap_location', '=', True), ('company_id', 'in', [company_id, False])], limit=1).id

    def doamin_location_scrap(self):
        if self.is_fual_expense:
            location_ids = self.env['stock.location'].search([('is_fual_expense', '=', True)])
            return [('id', 'in', location_ids.ids)]
        # else:
        #     location_ids = self.env['stock.location'].search([('scrap_location', '=', True)])
        #     return [('id', 'in', location_ids.ids)]

    is_fual_expense = fields.Boolean(string="Is Fual Expense Location")
    scrap_location_id = fields.Many2one(
        'stock.location', 'Scrap Location', domain=doamin_location_scrap, required=True, states={'done': [('readonly', True)]}, check_company=True)
    state = fields.Selection(
        selection_add = [
        ('draft', 'Draft'),
        ('procurement_manager', 'Procurement Manager'),
        ('finance','Finance Manager'),
        ('done', 'Stock Out'),
        ('cancel', 'Cancel')],
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
    fleet_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    odometer = fields.Float(string="Last Odometer", related="fleet_id.odometer")
    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    effective_date = fields.Date('Effective Date')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(StockScrap, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                submenu=submenu)
        print("========================================================", self._context.get('default_is_fual_expense'))
        if self._context.get('default_is_fual_expense'):

            fields = res.get('fields')
            print("YYYYYYYYYYYYYYYYYYYYYYYYY", fields)
            if fields:
                if fields.get('scrap_location_id'):
                    res['fields']['scrap_location_id']['string'] = _('Fuel Expense Location')
            # if view_type == 'form':
            #     view_id = self.env.ref('membership.membership_products_form').id
            # else:
            #     view_id = self.env.ref('membership.membership_products_tree').id
        return res

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


