from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    based_on = fields.Selection(
        selection=[('cash', 'Cash'), ('credit', 'Credit')],
        string='Based On',
    )
    is_casher_approved = fields.Boolean(string='Cashier Approved')
    is_casher_submitted = fields.Boolean(string='Submitted For Cashier')
    lead_id = fields.Many2one('crm.lead', string='Lead')

    def action_casher_approval_submit(self):
        self.write({'is_casher_submitted': True})

    def action_casher_approval(self):
        self.write({'is_casher_approved': True})


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    analytic_account_ids = fields.Many2many(
        'account.analytic.account',
        'account_analytic_account_sale_order_line_rel',
        'sale_order_line_id',
        'account_analytic_account_id',
        string='Analytic Accounts',
    )
