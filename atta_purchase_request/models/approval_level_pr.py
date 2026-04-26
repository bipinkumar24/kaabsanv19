# -*- coding: utf-8 -*-

from odoo import api, models, fields, _

class ApprovalLevelPR(models.Model):
    _name = 'approval.level.pr'
    _description = 'Approval Level Purchase Request'
    _order = 'level'

    name = fields.Char('Name')
    display_message = fields.Html('Display Message')
    level = fields.Integer('Level')
    is_last_approval = fields.Boolean('Is Last')
    is_reject = fields.Boolean('Is Reject')
    is_full_field = fields.Boolean(string="Is Full Fields")
    approval_user_ids = fields.Many2many('res.users', string='Approval User')
    group_ids = fields.Many2many('res.groups', 'res_groups_approval_rels', 'approval_id', 'group_id', string='Groups')
    fields_ids = fields.Many2many('ir.model.fields', string='Required Fields')

    @api.onchange('group_ids')
    def onchange_group_ids(self):
        for rec in self:
            users = []
            for group in rec.group_ids:
                users += group.users.ids
            rec.approval_user_ids = [(6, 0, users)]

class RemarksRefund(models.Model):
    _name = 'remarks.approval.pr'
    _description = 'Approval Remarks Purchase Request'
    _order = 'remark_datettime desc'

    purchase_request_id = fields.Many2one('purchase.request', string='Purchase Request')
    name = fields.Char('Remarks')
    user_id = fields.Many2one('res.users', string='User')
    remark_datettime = fields.Datetime(string='Remark Datetime')
    from_stage_id = fields.Many2one('approval.level.pr', string='From Stage', required=0)
    to_stage_id = fields.Many2one('approval.level.pr', string='To Stage')
    consumed_hours = fields.Char(string='Consumed Time')
    remark_type = fields.Selection([('approve', 'Approved'), ('previous', 'Previous'), ('reject', 'Reject')])
