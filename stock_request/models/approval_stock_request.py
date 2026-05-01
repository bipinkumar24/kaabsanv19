# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class ApprovalStockRequest(models.Model):
    _name = 'approval.stock.request'
    _description = 'Approval Stock Request'
    _order = 'level'

    name = fields.Char('Name')
    display_message = fields.Html('Display Message')
    level = fields.Integer('Level')
    is_last_approval = fields.Boolean('Is Last')
    is_reject = fields.Boolean('Is Reject')
    approval_user_ids = fields.Many2many(
        'res.users',
        'approval_stock_request_res_users_rel',
        'approval_stock_request_id',
        'res_users_id',
        string='Approval User',
    )
    group_ids = fields.Many2many('res.groups', 'res_groups_approval_stock', 'approval_id', 'group_id', string='Groups')
    fields_ids = fields.Many2many(
        'ir.model.fields',
        'approval_stock_request_ir_model_fields_rel',
        'approval_stock_request_id',
        'ir_model_fields_id',
        string='Required Fields',
    )

    @api.onchange('group_ids')
    def onchange_group_ids(self):
        for rec in self:
            users = []
            for group in rec.group_ids:
                users += group.users.ids
            rec.approval_user_ids = [(6, 0, users)]
