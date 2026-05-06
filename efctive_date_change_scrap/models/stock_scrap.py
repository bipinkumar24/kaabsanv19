from odoo import fields, models


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    is_fual_expense = fields.Boolean(string="Is Fual Expense Location")

    def action_change_effective_date(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Change Effective Date',
            'res_model': 'change.scrap.date.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_scrap_id': self.id},
        }
