import datetime
from odoo import fields, models, _
from odoo.exceptions import UserError


class ChangeScrapDateWizard(models.TransientModel):
    _name = 'change.scrap.date.wizard'
    _description = 'Change Scrap Effective Date'

    scrap_id = fields.Many2one('stock.scrap', string='Scrap Order', required=True, readonly=True)
    current_date = fields.Datetime(related='scrap_id.date_done', string='Current Done Date', readonly=True)
    current_effective_date = fields.Date(related='scrap_id.effective_date', string='Current Effective Date', readonly=True)
    effective_date = fields.Date(string='New Effective Date', required=True, default=fields.Date.today)

    def action_confirm(self):
        self.ensure_one()
        scrap = self.scrap_id
        new_date = self.effective_date

        if scrap.state not in ('done', 'validate'):
            raise UserError(_('You can only change the effective date of a validated scrap order.'))

        # Store at noon UTC so the date displays correctly in any timezone (UTC-11 to UTC+11)
        new_datetime = datetime.datetime.combine(new_date, datetime.time(12, 0, 0))

        # 1. Update scrap's effective_date and date_done
        scrap.sudo().write({
            'effective_date': new_date,
            'date_done': new_datetime,
        })

        # 2. Collect all stock moves (single-line and multi-line)
        all_moves = (scrap.move_ids | scrap.stock_move_ids).sudo()

        # 3. Update stock move dates (also updates move_line_ids.date automatically)
        if all_moves:
            all_moves.write({'date': new_datetime})

        # 4. Update journal entries linked to those moves
        journal_entries = all_moves.mapped('account_move_id').filtered(lambda m: m.id).sudo()
        for je in journal_entries:
            if je.state == 'posted':
                # Clear checked flag first (required by account's _sanitize_vals)
                if je.checked:
                    je.write({'checked': False})
                je.button_draft()
                je.write({'date': new_date})
                je._post(soft=False)
            elif je.state == 'draft':
                je.write({'date': new_date})

        return {'type': 'ir.actions.act_window_close'}
