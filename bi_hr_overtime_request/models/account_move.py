# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import datetime
import pytz
from odoo.exceptions import UserError, ValidationError


class HrDepartment(models.Model):
    _inherit = "hr.department"

    product_id = fields.Many2one('product.product', string='Overtime Product')


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_next_approval_id(self):
        rec = self.env['approval.level.account'].search([('level', '=', 1)])
        return rec.id

    def _get_next_approval_id_domain(self):
        return ['|', '|', ('is_last_approval', '=', True),
                ('is_reject', '=', True),
                ('is_finance_approval', '=', True)]

    is_overtime = fields.Boolean('Is Overtime')
    next_approval_id = fields.Many2one('approval.level.account', string='Next Approval', tracking=True,
                                       default=_get_next_approval_id, domain=_get_next_approval_id_domain)

    is_multiple_overtime_request = fields.Boolean('Is Multiple Overtime Request',
                                                  compute='_compute_is_overtime_request')
    is_single_overtime_request = fields.Boolean('Is Single Overtime Request',
                                                compute='_compute_is_overtime_request')

    multiple_overtime_request_id = fields.Many2one('multiple.overtime.request',
                                                   string='Multiple Overtime Request')
    overtime_request_id = fields.Many2one('overtime.request',
                                          compute='_compute_overtime_request_id',
                                          string='Overtime Request')

    def _compute_is_overtime_request(self):
        for rec in self:
            rec._compute_overtime_request_id()
            if rec.overtime_request_id:
                rec.is_single_overtime_request = True
                rec.is_multiple_overtime_request = False
            elif rec.multiple_overtime_request_id:
                rec.is_single_overtime_request = False
                rec.is_multiple_overtime_request = True
            else:
                rec.is_single_overtime_request = False
                rec.is_multiple_overtime_request = False

    def _compute_overtime_request_id(self):
        for rec in self:
            overtime_request_id = self.env['overtime.request'].search([('bill_id', '=', rec.id)])
            rec.overtime_request_id = overtime_request_id.id
