import datetime
from odoo import fields, models, _
from odoo.exceptions import UserError


class ChangeScrapDateWizard(models.TransientModel):
    _name = 'change.scrap.date.wizard'
    _description = 'Change Scrap Effective Date'

    scrap_id = fields.Many2one('stock.scrap', string='Scrap Order', required=True, readonly=True)
    current_date = fields.Datetime(related='scrap_id.date_done', string='Current Date', readonly=True)
    effective_date = fields.Date(string='New Effective Date', required=True, default=fields.Date.today)

    def action_confirm(self):
        self.ensure_one()
        scrap = self.scrap_id
        new_date = self.effective_date

        if scrap.state != 'done':
            raise UserError(_('You can only change the effective date of a validated scrap order.'))

        # Keep existing time component when updating date_done
        existing_time = scrap.date_done.time() if scrap.date_done else datetime.time.min
        new_datetime = datetime.datetime.combine(new_date, existing_time)
        scrap.write({'date_done': new_datetime})

        # Update journal entry on each related stock move
        for move in scrap.move_ids:
            journal_entry = move.account_move_id
            if not journal_entry:
                continue
            if journal_entry.state == 'posted':
                journal_entry.button_draft()
                journal_entry.write({'date': new_date})
                journal_entry.action_post()
            elif journal_entry.state == 'draft':
                journal_entry.write({'date': new_date})

        return {'type': 'ir.actions.act_window_close'}
