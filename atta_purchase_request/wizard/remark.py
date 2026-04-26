# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
import pytz
from odoo.exceptions import UserError, ValidationError


class Remark(models.TransientModel):
    _name = 'pr.remark.wizard'
    _inherits = {'mail.compose.message': 'composer_id'}
    _description = ""

    @api.model
    def default_get(self, fields):
        result = super(Remark, self).default_get(fields)
        result['purchase_request_id'] = self._context.get('active_id')
        return result

    purchase_request_id = fields.Many2one('purchase.request', string='Approval Refund')
    name = fields.Text('Remarks')
    display_message = fields.Html(string='Display Message')
    is_first_level = fields.Boolean('Is First Level?')
    email_from = fields.Char('From Email')
    email_to = fields.Char('To Email')
    composer_id = fields.Many2one('mail.compose.message', string='Composer', required=False)
    attachment_ids = fields.Many2many('ir.attachment', 'remark_attachmment_id',
                                      'remark_id', 'attachment_id', string='Attachments')
    body_html = fields.Html('Body', render_engine='qweb', translate=True, sanitize=False)
    is_send_email = fields.Boolean('Is Send Email')

    @api.onchange('purchase_request_id')
    def onchange_purchase_request_id(self):
        for rec in self:
            if rec.purchase_request_id:
                rec.display_message = self.purchase_request_id.next_approval_id.display_message
                if self.purchase_request_id.next_approval_id.level == 1:
                    rec.is_first_level = True
                else:
                    rec.is_first_level = False

    def approve(self):
        level_rec = self.env['approval.level.pr'].search([('level', '=', self.purchase_request_id.next_approval_id.level + 1)], limit=1)

        last_remark_id = self.env['remarks.approval.pr'].search([('purchase_request_id', '=', self.purchase_request_id.id)], limit=1, order='create_date desc')

        consumed_hours = 0
        d2 = fields.Datetime.now()
        if last_remark_id:
            d1 = last_remark_id.remark_datettime
            diff = d2 - d1
            consumed_hours = diff


        if not level_rec:
            raise UserError(_("Please Configure Approval Level First and Contact to Administrator"))
        self.purchase_request_id.remark_ids = [(0, 0, {'name': self.name,
                                           'user_id': self.env.user.id,
                                           'remark_datettime': fields.Datetime.now(),
                                           'consumed_hours': consumed_hours,
                                           'from_stage_id': self.purchase_request_id.next_approval_id.id,
                                           'to_stage_id': level_rec.id,
                                           'remark_type': 'approve'
                                           })]
        if self.purchase_request_id.next_approval_id.is_last_approval == True:
            if self.purchase_request_id.order_ids:
                purchase_not_done = self.purchase_request_id.order_ids.filtered(lambda x:x.state not in ['cancel', 'done', 'purchase'])
                if purchase_not_done:
                    raise ValidationError("Please Confirm Purchase Order")
                if self.purchase_request_id.order_ids.picking_ids:
                    picking_ids = self.purchase_request_id.order_ids.picking_ids
                    if all([picking.state != 'done' for picking in picking_ids.filtered(lambda x:x.state != 'cancel')]):
                        raise ValidationError("Please Complete The Receipt")
        if self.purchase_request_id.next_approval_id.is_last_approval == True:
            equipment_ids = self.env['allcation.request'].search([('purchase_request_id', '=', self.purchase_request_id.id)])
            if equipment_ids:
                equipment_approved_ids = equipment_ids.filtered(lambda x:x.state not in ['allocate', 'return', 'trans', 'cancel'])
                if equipment_approved_ids:
                    raise ValidationError("Allocation are Not allocate!.")
                equipment_picking_ids = equipment_approved_ids.mapped('picking_ids')
                if all([picking.state != 'done' for picking in equipment_picking_ids.filtered(lambda x:x.state != 'cancel')]):
                            raise ValidationError("Location Data Can not be Done")
        if self.purchase_request_id.next_approval_id.is_last_approval == True:
            expense_ids = self.env['stock.picking'].search([('purchase_request_id', '=', self.purchase_request_id.id)])
            if expense_ids:
                if all([picking.state != 'done' for picking in expense_ids.filtered(lambda x:x.state != 'cancel')]):
                    raise ValidationError("Location Data Can not be Done")
        self.purchase_request_id.next_approval_id = level_rec.id

    def previous(self):
        level_rec = self.env['approval.level.pr'].search([('level', '=', self.purchase_request_id.next_approval_id.level - 1)],
                                                          limit=1)
        last_remark_id = self.env['remarks.approval.pr'].search([('purchase_request_id', '=', self.purchase_request_id.id)], limit=1,
                                                                 order='create_date desc')

        consumed_hours = 0
        d2 = fields.Datetime.now()
        if last_remark_id:
            d1 = last_remark_id.remark_datettime
            diff = d2 - d1
            consumed_hours = diff
        if not level_rec:
            raise UserError(_("Please Configure Approval Level First and Contact to Administrator"))
        self.purchase_request_id.remark_ids = [(0, 0, {'name': self.name,
                                           'user_id': self.env.user.id,
                                           'remark_datettime': fields.Datetime.now(),
                                           'consumed_hours': consumed_hours,
                                           'from_stage_id': self.purchase_request_id.next_approval_id.id,
                                           'to_stage_id': level_rec.id,
                                           'remark_type': 'previous'
                                           })]
        self.purchase_request_id.next_approval_id = level_rec.id

    def reject(self):
        level_rec = self.env['approval.level.pr'].search([('is_reject', '=', True)], limit=1)
        if not level_rec:
            raise UserError(_("Please Configure Reject Level First or Contact to Administrator"))
        consumed_hours = 0
        last_remark_id = self.env['remarks.approval.pr'].search([('purchase_request_id', '=', self.purchase_request_id.id)], limit=1,
                                                                 order='create_date desc')
        d2 = fields.Datetime.now()
        if last_remark_id:
            d1 = last_remark_id.remark_datettime
            diff = d2 - d1
            consumed_hours = diff
        self.purchase_request_id.remark_ids = [(0, 0, {'name': self.name,
                                           'user_id': self.env.user.id,
                                           'remark_datettime': fields.Datetime.now(),
                                           'consumed_hours': consumed_hours,
                                           'from_stage_id': self.purchase_request_id.next_approval_id.id,
                                           'to_stage_id': level_rec.id,
                                           'remark_type': 'reject'
                                           })]
        self.purchase_request_id.next_approval_id = level_rec.id

