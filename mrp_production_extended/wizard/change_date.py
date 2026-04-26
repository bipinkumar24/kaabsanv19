from odoo import models, fields, api


class ChangeDate(models.TransientModel):
    _name = 'change.date'


    date = fields.Date(string='Date', default=fields.Date.today())

    def change_date(self):
        # Odoo 19 migration: keep the old misspelled context key for existing server actions.
        # Old debug prints kept for migration reference:
        # print("*****************", self._context.get('default_chage_date_ids', []))
        # print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", self.env['mrp.production'].browse(self._context.get('default_chage_date_ids', [])))
        production_ids = self._context.get('default_change_date_ids') or self._context.get('default_chage_date_ids', [])
        mrp_ids = self.env['mrp.production'].browse(production_ids)
        date_datetime = fields.Datetime.to_datetime(self.date)
        for mrp in mrp_ids:
            # Odoo 19 migration: stock.valuation.layer is no longer the live valuation record.
            # Old lookup kept for migration reference:
            # domain = [('id', 'in', (mrp.move_raw_ids + mrp.move_finished_ids + mrp.scrap_ids.move_id).stock_valuation_layer_ids.ids)]
            # valuation_ids = self.env['stock.valuation.layer'].search(domain)
            stock_moves = mrp.move_raw_ids | mrp.move_finished_ids | mrp.scrap_ids.move_id
            account_moves = stock_moves.mapped('account_move_id')
            posted_moves = account_moves.filtered(lambda move: move.state == 'posted')
            if posted_moves:
                posted_moves.button_draft()
            account_moves.write({'date': self.date})
            if posted_moves:
                posted_moves._post()
            stock_moves.write({'date': date_datetime})
            stock_moves.move_line_ids.write({'date': date_datetime})










