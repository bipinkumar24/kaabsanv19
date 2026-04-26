# -*- coding: utf-8 -*-

from odoo import api, models, fields, _

class ApprovalLevel(models.Model):
    _name = 'approval.level.crm'
    _description = 'Approval Level CRM'
    _order = 'level'

    name = fields.Char('Name')
    display_message = fields.Html('Display Message')
    level = fields.Integer('Level')
    is_last_approval = fields.Boolean('Is Last')
    is_reject = fields.Boolean('Is Reject')
    approval_user_ids = fields.Many2many('res.users', string='Approval User')
    is_customer_doc_required = fields.Boolean('Is Customer Doc Required')
    fields_ids = fields.Many2many('ir.model.fields', string='Required Fields')
    is_send_email = fields.Boolean('Is Send Email')



class RemarksRefund(models.Model):
    _name = 'remarks.approval.crm'
    _description = 'Approval Remarks CRM'
    _order = 'remark_datettime desc'

    lead_id = fields.Many2one('crm.lead', string='Lead')
    name = fields.Char('Remarks')
    user_id = fields.Many2one('res.users', string='User')
    remark_datettime = fields.Datetime(string='Remark Datetime')
    from_stage_id = fields.Many2one('approval.level.crm', string='From Stage', required=0)
    to_stage_id = fields.Many2one('approval.level.crm', string='To Stage')
    consumed_hours = fields.Char(string='Consumed Time')
    remark_type = fields.Selection([('approve', 'Approved'), ('previous', 'Previous'), ('reject', 'Reject')])