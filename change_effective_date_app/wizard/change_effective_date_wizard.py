# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import UserError


class ChangeEffectiveDateWizard(models.TransientModel):
    _name = "change.effective.date.wizard"
    _description = "Create Add Date Invoice"

    date_done = fields.Datetime('Effective Date')
    all_picking = fields.Boolean(string='Apply All Picking')
    picking_id = fields.Many2one('stock.picking', string='Picking')

    def _get_target_pickings(self):
        self.ensure_one()
        if self.all_picking:
            return self.env['stock.picking'].search([('state', '=', 'done')])

        if self.env.context.get('from_server_action'):
            picking_ids = self.env.context.get('default_change_dates_ids', [])
            return self.env['stock.picking'].browse(picking_ids).filtered(lambda p: p.state == 'done')

        return self.picking_id.filtered(lambda p: p.state == 'done')

    def _update_picking_effective_date(self, picking):
        moves = picking.move_ids
        move_lines = picking.move_line_ids
        # Odoo 19 no longer exposes the old stock.valuation.layer model.
        # valuation_layers = self.env['stock.valuation.layer'].search([
        #     ('stock_move_id', 'in', moves.ids)
        # ])
        account_moves = moves.mapped('account_move_id')

        picking.write({'date_done': self.date_done})
        if moves:
            moves.write({'date': self.date_done})
        if move_lines:
            move_lines.write({'date': self.date_done})
        if account_moves:
            account_moves.write({'date': self.date_done})
        # if valuation_layers:
        #     self.env.cr.execute(
        #         "UPDATE stock_valuation_layer SET create_date = %s WHERE id IN %s",
        #         (self.date_done, tuple(valuation_layers.ids)),
        #     )

    def update_effective_date(self):
        for rec in self:
            if not rec.date_done:
                raise UserError(_("Please select an effective date."))

            pickings = rec._get_target_pickings()
            if not pickings:
                raise UserError(_("No completed picking was found to update."))

            for picking in pickings:
                rec._update_picking_effective_date(picking)
