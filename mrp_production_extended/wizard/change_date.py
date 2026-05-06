from odoo import models, fields, api


class ChangeDate(models.TransientModel):
    _name = 'change.date'


    date = fields.Date(string='Date', default=fields.Date.today())

    # def change_date(self):
    #     print("*****************", self._context.get('default_chage_date_ids',[]))
    #     print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", self.env['mrp.production'].browse(self._context.get('default_chage_date_ids',[])))
    #     mrp_ids = self.env['mrp.production'].browse(self._context.get('default_chage_date_ids',[]))
    #     for mrp in mrp_ids:
    #         domain = [('id', 'in',(mrp.move_raw_ids + mrp.move_finished_ids + mrp.scrap_ids.move_id).stock_valuation_layer_ids.ids)]
    #         valuation_ids = self.env['stock.valuation.layer'].search(domain)
    #         for valuation in valuation_ids:
    #             if valuation.account_move_id:
    #                 valuation.account_move_id.date = self.date
    #             if valuation.stock_move_id:
    #                 valuation.stock_move_id.date = self.date
    #                 stock_move_line_ids = self.env['stock.move.line'].search([('move_id', '=', valuation.stock_move_id.id)])
    #                 stock_move_line_ids.write({'date': self.date})

    def _get_move_account_moves(self, move):
        account_moves = self.env['account.move']
        if 'account_move_id' in move._fields:
            account_moves |= move.account_move_id
        if 'account_move_ids' in move._fields:
            account_moves |= move.account_move_ids
        return account_moves

    def _update_account_move_date(self, account_moves):
        for account_move in account_moves:
            if account_move.state == 'posted':
                if 'checked' in account_move._fields and account_move.checked:
                    account_move.write({'checked': False})
                account_move.button_draft()
                account_move.write({'date': self.date})
                account_move.action_post()
            else:
                account_move.write({'date': self.date})

    def change_date(self):
        print("*****************", self._context.get('default_chage_date_ids',[]))
        print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", self.env['mrp.production'].browse(self._context.get('default_chage_date_ids',[])))
        mrp_ids = self.env['mrp.production'].browse(
            self._context.get('default_chage_date_ids', [])
        )

        for mrp in mrp_ids:
            if 'accounting_date' in mrp._fields:
                mrp.accounting_date = self.date

            scrap_moves = mrp.scrap_ids.move_ids
            all_moves = mrp.move_raw_ids + mrp.move_finished_ids + scrap_moves
            account_moves = self.env['account.move'].search([('ref', 'ilike', mrp.name)])

            for move in all_moves:
                move.date = self.date
                move.move_line_ids.write({'date': self.date})
                account_moves |= self._get_move_account_moves(move)

            self._update_account_move_date(account_moves)







