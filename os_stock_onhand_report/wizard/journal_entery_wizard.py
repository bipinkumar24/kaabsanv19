# -*- coding: utf-8 -*-
from odoo import fields, models


class LinkJournalEntryWizard(models.TransientModel):
    _name = "link.journal.entry.wizard"
    _description = "Wizard to link Journal Entry to Stock Move"

    move_id = fields.Many2one("stock.move", string="Stock Move")
    journal_entry_id = fields.Many2one("account.move", string="Journal Entry", domain=[("move_type", "=", "entry")])

    def action_link_journal_entry(self):
        self.journal_entry_id.write({"stock_move_id": self.move_id.id})
