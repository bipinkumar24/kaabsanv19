# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ChangeEffectiveDateWizard(models.TransientModel):
    _name = "change.effective.date.wizard"
    _description = "Create Add Date Invoice"

    date_done = fields.Datetime('Effective Date')
    all_picking = fields.Boolean(string='Apply All Picking')
    picking_id = fields.Many2one('stock.picking', string='Picking')

    def _update_expense_account_move_date(self, picking, date_done):
        if 'expense_account_move_id' not in picking._fields or not picking.expense_account_move_id:
            return

        account_move = picking.expense_account_move_id
        move_date = fields.Date.to_date(date_done)
        if account_move.state == 'posted':
            account_move.button_draft()
            account_move.write({'date': move_date})
            account_move.action_post()
        else:
            account_move.write({'date': move_date})

    def update_effective_date(self):
        for rec in self:
            if not rec.all_picking:
                if self.env.context.get('from_server_action'):
                    picking_ids = self.env['stock.picking'].browse(self.env.context.get('default_change_dates_ids'))
                    for picking in picking_ids:
                        rec.picking_id = picking.id
                        rec.picking_id.date_done = rec.date_done
                        rec._update_expense_account_move_date(rec.picking_id, rec.date_done)
                        move_ids = self.env['stock.move'].search([('reference', '=', rec.picking_id.name)])
                        move_line_ids = self.env['stock.move.line'].search([('reference', '=', rec.picking_id.name)])
                        for move_id in move_ids:
                            move_id.date = rec.date_done
                            if 'stock.valuation.layer' in self.env:
                                valuation_ids = self.env['stock.valuation.layer'].search([('stock_move_id', '=', move_id.id)])
                                for valuation_id in valuation_ids:
                                    self.env.cr.execute("UPDATE stock_valuation_layer set create_date = '%s' WHERE id=%s" % (
                                        rec.date_done, valuation_id.id))
                                account_move_ids = self.env['account.move'].search([('stock_move_id', '=', move_id.id)])
                                for account_move_id in account_move_ids:
                                    account_move_id.date = rec.date_done
                        for move_line_id in move_line_ids:
                            move_line_id.date = rec.date_done
                else:
                    rec.picking_id.date_done = rec.date_done
                    rec._update_expense_account_move_date(rec.picking_id, rec.date_done)
                    move_ids = self.env['stock.move'].search([('reference', '=', rec.picking_id.name)])
                    move_line_ids = self.env['stock.move.line'].search([('reference', '=', rec.picking_id.name)])
                    for move_id in move_ids:
                        move_id.date = rec.date_done
                        if 'stock.valuation.layer' in self.env:
                            valuation_ids = self.env['stock.valuation.layer'].search([('stock_move_id', '=', move_id.id)])
                            for valuation_id in valuation_ids:
                                self.env.cr.execute("UPDATE stock_valuation_layer set create_date = '%s' WHERE id=%s" % (
                                    rec.date_done, valuation_id.id))
                            account_move_ids = self.env['account.move'].search([('stock_move_id', '=', move_id.id)])
                            for account_move_id in account_move_ids:
                                account_move_id.date = rec.date_done
                    for move_line_id in move_line_ids:
                        move_line_id.date = rec.date_done
            else:
                picking_ids = self.env['stock.picking'].search([('state', '=', 'done')])
                for picking_id in picking_ids:
                    picking_id.date_done = rec.date_done
                    rec._update_expense_account_move_date(picking_id, rec.date_done)
                    move_ids = self.env['stock.move'].search([('reference', '=', picking_id.name)])
                    move_line_ids = self.env['stock.move.line'].search([('reference', '=', picking_id.name)])
                    for move_id in move_ids:
                        move_id.date = rec.date_done
                        if 'stock.valuation.layer' in self.env:
                            valuation_ids = self.env['stock.valuation.layer'].search([('stock_move_id', '=', move_id.id)])
                            for valuation_id in valuation_ids:
                                self.env.cr.execute("UPDATE stock_valuation_layer set create_date = '%s' WHERE id=%s" % (
                                    rec.date_done, valuation_id.id))
                            account_move_ids = self.env['account.move'].search([('stock_move_id', '=', move_id.id)])
                            for account_move_id in account_move_ids:
                                account_move_id.date = rec.date_done

                    for move_line_id in move_line_ids:
                        move_line_id.date = rec.date_done
