# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
import pytz
from odoo.exceptions import UserError, ValidationError


class SrRemarkWizard(models.TransientModel):
    _name = 'sr.remark.wizard'
    _inherits = {'mail.compose.message': 'composer_id'}
    _description = ""

    @api.model
    def default_get(self, fields):
        result = super(SrRemarkWizard, self).default_get(fields)
        stock_request_id = self._context.get('active_id')
        composer = self.env['mail.compose.message'].create({
            'model': 'stock.request',
            'res_ids': str([stock_request_id]) if stock_request_id else False,
            'composition_mode': 'comment',
        })
        result['composer_id'] = composer.id
        result['stock_request_id'] = stock_request_id
        return result

    stock_request_id = fields.Many2one('stock.request', string='Approval Refund')
    name = fields.Text('Remarks')
    display_message = fields.Html(string='Display Message')
    is_first_level = fields.Boolean('Is First Level?')
    email_from = fields.Char('From Email')
    email_to = fields.Char('To Email')
    composer_id = fields.Many2one(
        'mail.compose.message',
        string='Composer',
        required=True,
        delegate=True,
        ondelete='cascade',
    )
    attachment_ids = fields.Many2many('ir.attachment', 'remark_attachmment_id_sr',
                                      'remark_id', 'attachment_id', string='Attachments')
    body_html = fields.Html('Body', render_engine='qweb', translate=True, sanitize=False)
    is_send_email = fields.Boolean('Is Send Email')

    @api.onchange('stock_request_id')
    def onchange_purchase_request_id(self):
        for rec in self:
            if rec.stock_request_id:
                rec.display_message = self.stock_request_id.next_approval_id.display_message
                if self.stock_request_id.next_approval_id.level == 1:
                    rec.is_first_level = True
                else:
                    rec.is_first_level = False

    def approve(self):
        level_rec = self.env['approval.stock.request'].search([('level', '=', self.stock_request_id.next_approval_id.level + 1)], limit=1)
        self.stock_request_id.next_approval_id = level_rec.id

    def previous(self):
        level_rec = self.env['approval.stock.request'].search([('level', '=', self.stock_request_id.next_approval_id.level - 1)],
                                                          limit=1)
        self.stock_request_id.next_approval_id = level_rec.id

    def reject(self):
        level_rec = self.env['approval.stock.request'].search([('is_reject', '=', True)], limit=1)
        if not level_rec:
            raise UserError(_("Please Configure Reject Level First or Contact to Administrator"))
        self.stock_request_id.next_approval_id = level_rec.id
