# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
import pytz
from odoo.exceptions import UserError, ValidationError


class Remark(models.TransientModel):
    _name = 'remark.remark.wizard'
    _description = "Picking Order"

    @api.model
    def default_get(self, fields):
        result = super(Remark, self).default_get(fields)
        result['approval_refund_id'] = self._context.get('active_id')
        return result

    approval_refund_id = fields.Many2one('stock.picking', string='Approval Refund')
    name = fields.Text('Remarks')

    def approve(self):
        level_rec = self.env['approval.level'].search([('level', '=', self.approval_refund_id.next_approval_id.level + 1)], limit=1)
        if not level_rec:
            raise UserError(_("Please Configure Approval Level First and Contact to Administrator"))

        self.approval_refund_id.next_approval_id = level_rec.id

    def reject(self):
        level_rec = self.env['approval.level'].search([('is_reject', '=', True)], limit=1)
        if not level_rec:
            raise UserError(_("Please Configure Reject Level First or Contact to Administrator"))
        self.approval_refund_id.next_approval_id = level_rec.id

