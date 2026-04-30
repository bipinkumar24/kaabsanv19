# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models

class AccountMove(models.Model):
    _inherit = "account.move"

    def action_set_to_draft_entry(self):
        posted_moves = self.filtered(lambda move: move.state == "posted")
        if posted_moves:
            posted_moves.button_draft()

    def action_cancel_entry(self):
        posted_moves = self.filtered(lambda move: move.state == "posted")
        if posted_moves:
            posted_moves.button_draft()
            posted_moves.button_cancel()

        draft_moves = (self - posted_moves).filtered(lambda move: move.state == "draft")
        if draft_moves:
            draft_moves.button_cancel()
