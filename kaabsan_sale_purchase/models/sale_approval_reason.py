from odoo import fields, models


class SaleApprovalReason(models.Model):
    _name = 'sale.approval.reason'
    _description = 'Sale Approval Reason'

    approval_for = fields.Selection(
        selection=[
            ('discount', 'Discount'),
            ('credit', 'Credit'),
            ('other', 'Other'),
        ],
        string='Approval For',
    )
    requested_discount = fields.Float(string='Requested Discount')
    notes = fields.Text(string='Notes')
