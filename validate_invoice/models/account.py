# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    state = fields.Selection(
        selection_add=[('preposted', 'Pre-posted')],
        ondelete={'preposted': 'set default'},
    )

    def button_prepost(self):
        self.write({'state': 'preposted'})

    def action_prepost(self):
        if not self.invoice_line_ids:
            raise UserError(_("You need to add a line before Pre-posting."))
        self.write({'state': 'preposted'})


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    state = fields.Selection(
        selection_add=[('preposted', 'Pre-posted')],
        ondelete={'preposted': 'set default'},
    )

    def action_post(self):
        ''' draft -> posted '''
        return super().action_post()

    def action_prepost(self):
        self.write({'state': 'preposted'})
        self.move_id.action_prepost()
        
    
    def action_draft(self):
        ''' posted -> draft '''
        return super().action_draft()
        
    
