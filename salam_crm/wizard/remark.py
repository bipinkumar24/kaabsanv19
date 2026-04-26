# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class Remark(models.TransientModel):
    _name = 'crm.remark.wizard'
    _inherits = {'mail.compose.message': 'composer_id'}
    _description = "CRM Lead"

    @api.model
    def default_get(self, field_list):
        result = super(Remark, self).default_get(field_list)
        lead = self.env['crm.lead'].browse(self.env.context.get('active_id'))
        composer = self.env['mail.compose.message'].create({
            'model': 'crm.lead',
            'res_ids': str([lead.id]) if lead else False,
            'composition_mode': 'comment',
        })
        result['composer_id'] = composer.id
        result['lead_id'] = lead.id
        if lead:
            result['display_message'] = lead.next_approval_id.display_message
            result['is_first_level'] = lead.next_approval_id.level == 1
            result['is_send_email'] = lead.next_approval_id.is_send_email
        return result

    lead_id = fields.Many2one('crm.lead', string='Approval Refund')
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
    attachment_ids = fields.Many2many('ir.attachment', 'remark_attachment_id_crm',
                                      'remark_id', 'attachment_id', string='Attachments')
    body_html = fields.Html('Body', render_engine='qweb', translate=True, sanitize=False)
    is_send_email = fields.Boolean('Is Send Email')

    @api.onchange('lead_id')
    def onchange_lead_id(self):
        for rec in self:
            if rec.lead_id:
                rec.display_message = rec.lead_id.next_approval_id.display_message
                rec.is_first_level = rec.lead_id.next_approval_id.level == 1
                rec.is_send_email = rec.lead_id.next_approval_id.is_send_email

    def _send_email_if_needed(self):
        self.ensure_one()
        if not self.is_send_email:
            return
        self.composer_id.write({
            'model': 'crm.lead',
            'res_ids': str([self.lead_id.id]) if self.lead_id else False,
            'composition_mode': 'comment',
            'attachment_ids': [(6, 0, self.attachment_ids.ids)],
        })
        self.composer_id._action_send_mail()

    def approve(self):
        self.ensure_one()
        level_rec = self.env['approval.level.crm'].search([('level', '=', self.lead_id.next_approval_id.level + 1)], limit=1)

        last_remark_id = self.env['remarks.approval.crm'].search([('lead_id', '=', self.lead_id.id)], limit=1, order='create_date desc')

        consumed_hours = 0
        d2 = fields.Datetime.now()
        if last_remark_id:
            d1 = last_remark_id.remark_datettime
            diff = d2 - d1
            consumed_hours = diff


        if not level_rec:
            raise UserError(_("Please Configure Approval Level First and Contact to Administrator"))
        self._send_email_if_needed()
        self.lead_id.remark_ids = [(0, 0, {'name': self.name,
                                           'user_id': self.env.user.id,
                                           'remark_datettime': fields.Datetime.now(),
                                           'consumed_hours': consumed_hours,
                                           'from_stage_id': self.lead_id.next_approval_id.id,
                                           'to_stage_id': level_rec.id,
                                           'remark_type': 'approve'
                                           })]
        self.lead_id.next_approval_id = level_rec.id

    def previous(self):
        self.ensure_one()
        level_rec = self.env['approval.level.crm'].search([('level', '=', self.lead_id.next_approval_id.level - 1)],
                                                          limit=1)
        last_remark_id = self.env['remarks.approval.crm'].search([('lead_id', '=', self.lead_id.id)], limit=1,
                                                                 order='create_date desc')

        consumed_hours = 0
        d2 = fields.Datetime.now()
        if last_remark_id:
            d1 = last_remark_id.remark_datettime
            diff = d2 - d1
            consumed_hours = diff
        if not level_rec:
            raise UserError(_("Please Configure Approval Level First and Contact to Administrator"))
        self._send_email_if_needed()
        self.lead_id.remark_ids = [(0, 0, {'name': self.name,
                                           'user_id': self.env.user.id,
                                           'remark_datettime': fields.Datetime.now(),
                                           'consumed_hours': consumed_hours,
                                           'from_stage_id': self.lead_id.next_approval_id.id,
                                           'to_stage_id': level_rec.id,
                                           'remark_type': 'previous'
                                           })]
        self.lead_id.next_approval_id = level_rec.id

    def reject(self):
        self.ensure_one()
        level_rec = self.env['approval.level.crm'].search([('is_reject', '=', True)], limit=1)
        if not level_rec:
            raise UserError(_("Please Configure Reject Level First or Contact to Administrator"))
        consumed_hours = 0
        last_remark_id = self.env['remarks.approval.crm'].search([('lead_id', '=', self.lead_id.id)], limit=1,
                                                                 order='create_date desc')
        d2 = fields.Datetime.now()
        if last_remark_id:
            d1 = last_remark_id.remark_datettime
            diff = d2 - d1
            consumed_hours = diff
        self._send_email_if_needed()
        self.lead_id.remark_ids = [(0, 0, {'name': self.name,
                                           'user_id': self.env.user.id,
                                           'remark_datettime': fields.Datetime.now(),
                                           'consumed_hours': consumed_hours,
                                           'from_stage_id': self.lead_id.next_approval_id.id,
                                           'to_stage_id': level_rec.id,
                                           'remark_type': 'reject'
                                           })]
        self.lead_id.next_approval_id = level_rec.id
