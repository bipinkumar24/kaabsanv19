# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

class ApprovalLevel(models.Model):
    _name = 'approval.level'
    _description = 'Approval Level'
    _order = 'level'

    name = fields.Char('Name')
    level = fields.Integer('Level')
    is_last_approval = fields.Boolean('Is Last')
    is_reject = fields.Boolean('Is Reject')
    approval_user_id = fields.Many2many('res.users', string='Approval User')


class StockMove(models.Model):
    _inherit = 'stock.move'

    is_expense = fields.Boolean(related='picking_id.is_expense', store=True, readonly=True)
    expense_picking_type_id = fields.Many2one(related='picking_id.expense_picking_type_id', store=True, readonly=True)
    is_button = fields.Boolean(
        related='picking_id.is_button',
        string='Is button',
        store=True,
        readonly=True
    )
    is_last_lavel = fields.Boolean('Is button', related='picking_id.is_last_lavel')

class Picking(models.Model):
    _inherit = "stock.picking"

    def action_unpost_entery(self):
        for picking in self:
            move = picking.expense_account_move_id
            if not move:
                raise UserError(_('No journal entry linked to this picking.'))
            if move.state == 'posted':
                move.button_draft()
            picking.sudo().write({
                'state': 'done',
                'is_posted': False,
            })

    is_expense = fields.Boolean('Is Expense')

    def _compute_sale_date(self):
        for rec in self:
            sale_order_id = self.env['sale.order'].search([('name', '=', rec.origin)])
            rec.sale_delivery_date = sale_order_id.date_order

    sale_delivery_date = fields.Datetime(string='Sale Delivery date', compute='_compute_sale_date')

    def _set_scheduled_date(self):
        for picking in self:
            # if picking.state in ('done', 'cancel'):
            #     raise UserError(_("You cannot change the Scheduled Date on a done or cancelled transfer."))
    #         rec.sudo().mapped('move_ids_without_package').mapped(
    # 'move_line_ids').sudo().write({'state': 'draft'})
            picking.move_line_ids.write({'date': picking.scheduled_date})


    def get_expense_operation_type(self):
        expense_operation_type_id = self.env['stock.picking.type'].search([('sequence_code', '=', 'EXP')])
        if expense_operation_type_id:
            return expense_operation_type_id[0].id
        else:
            return False
    expense_picking_type_id = fields.Many2one('stock.picking.type', string='Expense Operation Type', default=get_expense_operation_type)
    employee_id = fields.Many2one('hr.employee', 'Employee')
    expense_account_move_id = fields.Many2one('account.move', string='Journal Entry', copy=False, readonly=True)

    def action_validate_data(self):
        AccountMove = self.env['account.move']
        Journal = self.env['account.journal']

        for picking in self:

            # 🔹 Get journal (company safe)
            journal = Journal.search([
                ('type', '=', 'general'),
                ('company_id', '=', picking.company_id.id)
            ], limit=1)

            if not journal:
                raise UserError("Please configure a General Journal.")

            # 🔹 Find existing journal entry
            account_move = picking.expense_account_move_id or AccountMove.search([
                ('ref', '=', picking.name),
                ('journal_id', '=', journal.id),
                ('company_id', '=', picking.company_id.id),
            ], limit=1)

            debit_map = {}
            credit_map = {}

            # 🔹 Loop moves (Odoo 19 fields)
            for move in picking.move_ids:

                product = move.product_id

                # ✅ Correct qty field in Odoo 19
                qty = move.quantity or move.product_uom_qty

                cost = product.standard_price or 0.0
                value = qty * cost

                print(value, "valuesssssssss")
                if not value:
                    continue

                # In Odoo 19, output account moved from product.category to stock.location
                stock_account = product.categ_id.property_stock_valuation_account_id
                output_account = picking.property_stock_account_output_categ_id

                print(stock_account, output_account, "output_accounts056789876")

                if not stock_account or not output_account:
                    continue

                # 🔹 Group debit
                debit_map[output_account.id] = debit_map.get(output_account.id, 0.0) + value

                # 🔹 Group credit
                credit_map[stock_account.id] = credit_map.get(stock_account.id, 0.0) + value

            move_lines = []

            # 🔹 Debit lines
            for acc_id, amount in debit_map.items():
                move_lines.append((0, 0, {
                    'name': picking.name,
                    'account_id': acc_id,
                    'debit': amount,
                    'credit': 0.0,
                }))

            # 🔹 Credit lines
            for acc_id, amount in credit_map.items():
                move_lines.append((0, 0, {
                    'name': picking.name,
                    'account_id': acc_id,
                    'debit': 0.0,
                    'credit': amount,
                }))

            if not move_lines:
                continue

            # 🔹 Create or update journal entry
            if account_move:
                if account_move.state == 'posted':
                    account_move.button_draft()

                account_move.line_ids.unlink()

                account_move.write({
                    'line_ids': move_lines,
                    'date': fields.Date.context_today(self),
                })
            else:
                account_move = AccountMove.create({
                    'journal_id': journal.id,
                    'date': fields.Date.context_today(self),
                    'ref': picking.name,
                    'line_ids': move_lines,
                    'company_id': picking.company_id.id,
                })

            # 🔹 Post entry
            account_move.action_post()

            print(account_move, "account_movessssssssssssssss", "hellllllllll")

            # 🔹 Update picking
            picking.write({
                'state': 'validate',
                'is_posted': True,
                'expense_account_move_id': account_move.id,
            })

    def action_view_journal_entry(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Entry'),
            'res_model': 'account.move',
            'res_id': self.expense_account_move_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_unpost_entry(self):
        for picking in self:
            move = picking.expense_account_move_id
            if not move:
                raise UserError(_('No journal entry linked to this picking.'))
            if move.state == 'posted':
                move.button_draft()

    def button_validate(self):
        for rec in self:
            if rec.is_expense:
                # for product in rec.move_line_ids_without_package:
                for product in rec.move_line_ids.filtered(lambda ml: not ml.package_id):
                    if product.product_id.standard_price <= 0:
                        raise UserError(_('Please Enter Product Cost!'))
                    product.product_id.old_categ_id = product.product_id.categ_id.id
                    product.product_id.categ_id = self.env.ref("salam_expense.product_category_expense_transfer").id
        res = super(Picking, self).button_validate()
        for rec in self:
            if rec.is_expense:
                for product in rec.move_line_ids.filtered(lambda ml: not ml.package_id):
                    product.product_id.sudo().write({'categ_id': product.product_id.old_categ_id})
        return res

    # def action_create_inventory_valuation_entry(self):
    #     for rec in self:
    #         # for product in rec.move_line_ids_without_package:
    #         for product in rec.move_line_ids.filtered(lambda ml: not ml.package_id):
    #             if product.product_id.standard_price <= 0:
    #                 raise UserError(_('Please Enter Product Cost!'))

    #         scraps = self.env['stock.scrap'].search([('picking_id', '=', rec.id)])
    #         print("----------- SCRAPS >>>>>>>>",scraps,rec.move_ids,scraps.move_ids)
    #         svl = self.env['stock.valuation.layer'].browse((rec.move_ids + scraps.move_ids).stock_valuation_layer_ids.ids)
    #         print("\n------------ SVL",svl)

    #         if svl.account_move_id:
    #             raise UserError(_(rec.name + ' has already accounting entry generated!'))

    #         svl.sudo().unlink()
    #         # for move_line in rec.move_line_ids_without_package:
    #         for move_line in rec.move_line_ids.filtered(lambda ml: not ml.package_id):
    #             move = move_line.move_id
    #             rounding = move.product_id.uom_id.rounding
    #             diff = move_line.qty_done
    #             if float_is_zero(diff, precision_rounding=rounding):
    #                 continue
    #             move_line._create_correction_svl(move, diff)


    def action_create_inventory_valuation_entry(self):
        for rec in self:

            for product in rec.move_line_ids.filtered(lambda ml: not ml.package_id):
                if product.product_id.standard_price <= 0:
                    raise UserError(_('Please Enter Product Cost!'))

            scraps = self.env['stock.scrap'].search([('picking_id', '=', rec.id)])

            moves = rec.move_ids | scraps.move_ids

            print("--------------------------- ",self.env['ir.module.module'].search([('name','=','stock_account')]).mapped('state'))

            svl = self.env['stock.valuation.layer'].search([
                ('stock_move_id', 'in', moves.ids)
            ])

            if svl.mapped('account_move_id'):
                raise UserError(_('%s has already accounting entry generated!') % rec.name)

            svl.sudo().unlink()

            for move_line in rec.move_line_ids.filtered(lambda ml: not ml.package_id):
                move = move_line.move_id
                rounding = move.product_id.uom_id.rounding
                diff = move_line.qty_done

                if float_is_zero(diff, precision_rounding=rounding):
                    continue

                move_line._create_correction_svl(move, diff)

    @api.depends('next_approval_id', 'next_approval_id.approval_user_id')
    def _compute_next_approval_user_id(self):
        for rec in self:
            rec.next_approval_user_id = [(6, 0, rec.next_approval_id.approval_user_id.ids)]

    @api.depends('next_approval_id', 'next_approval_user_id')
    def _compute_is_button(self):
        for rec in self:
            print()
            if self.env.user.id in rec.next_approval_user_id.ids:
                rec.is_button = True
            else:
                rec.is_button = False

            if rec.next_approval_id.is_last_approval or rec.next_approval_id.is_reject:
                rec.is_button = False
            if rec.next_approval_id.is_last_approval:
                rec.is_last_lavel = True
            else:
                rec.is_last_lavel = False


    def _get_next_approval_id(self):
        rec = self.env['approval.level'].search([('level', '=', 1)])
        return rec.id

    next_approval_id = fields.Many2one('approval.level', string='Next Approval', required=False, tracking=True,
                                       default=_get_next_approval_id)
    next_approval_user_id = fields.Many2many('res.users', string='Next Approval User',
                                            compute='_compute_next_approval_user_id', store=True)
    is_button = fields.Boolean('Is button', compute='_compute_is_button')
    is_last_lavel = fields.Boolean('Is button', compute='_compute_is_button')

    property_valuation = fields.Selection([
        ('manual_periodic', 'Manual'),
        ('real_time', 'Automated')], string='Inventory Valuation',
        default="real_time",
        company_dependent=True, copy=True,
        help="""Manual: The accounting entries to value the inventory are not posted automatically.
            Automated: An accounting entry is automatically created to value the inventory when a product enters or leaves the company.
            """)

    property_stock_journal = fields.Many2one(
        'account.journal', 'Stock Journal', company_dependent=True,
        domain="[('company_id', '=', allowed_company_ids[0])]", check_company=True,
        help="When doing automated inventory valuation, this is the Accounting Journal in which entries will be automatically posted when stock moves are processed.")
    property_stock_account_input_categ_id = fields.Many2one(
        'account.account', 'Stock Input Account', company_dependent=True,
        domain="[('company_ids', 'parent_of', allowed_company_ids[0])]", check_company=True,
        help="""Counterpart journal items for all incoming stock moves will be posted in this account, unless there is a specific valuation account
                    set on the source location. This is the default value for all products in this category. It can also directly be set on each product.""")
    property_stock_account_output_categ_id = fields.Many2one(
        'account.account', 'Stock Output Account', company_dependent=True, check_company=True,
        help="""When doing automated inventory valuation, counterpart journal items for all outgoing stock moves will be posted in this account,
                    unless there is a specific valuation account set on the destination location. This is the default value for all products in this category.
                    It can also directly be set on each product.""")
    property_stock_valuation_account_id = fields.Many2one(
        'account.account', 'Stock Valuation Account', company_dependent=True,
        domain="[('company_ids', 'parent_of', allowed_company_ids[0])]", check_company=True,
        help="""When automated inventory valuation is enabled on a product, this account will hold the current value of the products.""", )

    @api.depends('state', 'move_lines')
    def _compute_show_mark_as_todo(self):
        res = super(Picking, self)._compute_show_mark_as_todo()
        for picking in self:
            if picking.is_expense:
                picking.show_mark_as_todo = False
                if picking.is_last_lavel:
                    picking.show_mark_as_todo = True
                    if picking.state != 'draft':
                        picking.show_mark_as_todo = False
        return res

    @api.constrains('property_stock_valuation_account_id', 'property_stock_account_output_categ_id',
                    'property_stock_account_input_categ_id')
    def _check_valuation_accouts(self):
        # Prevent to set the valuation account as the input or output account.
        for rec in self:
            valuation_account = rec.property_stock_valuation_account_id
            input_and_output_accounts = rec.property_stock_account_input_categ_id | rec.property_stock_account_output_categ_id
            if valuation_account and valuation_account in input_and_output_accounts:
                raise ValidationError(
                    _('The Stock Input and/or Output accounts cannot be the same as the Stock Valuation account.'))

    def action_approve(self):
        view_id = self.env.ref('salam_expense.remark_remark_wizard_wizard_view').id
        return {'type': 'ir.actions.act_window',
                'name': _('Remarks'),
                'res_model': 'remark.remark.wizard',
                'target': 'new',
                'view_mode': 'form',
                'views': [[view_id, 'form']],
                }

    @api.onchange('is_expense')
    def onchange_is_expense(self):
        for rec in self:
            if rec.is_expense:
                expense_operation_type_id = self.env['stock.picking.type'].search([('sequence_code', '=', 'EXP')])
                return {'domain': {'picking_type_id': [('id', 'in', expense_operation_type_id.ids)]}}

    def sh_cancel(self):
        is_internal_transfer = any(picking.is_expense for picking in self)
        if not is_internal_transfer:
            print("-------------- NOT INTERNAL TRANSFER >>>>>>>>>>>>>>")
            self.unlink()
            return {
                'name': 'Transfers',
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_type': 'form',
                'view_mode': 'list,kanban,form,calendar',
                'search_view_id': [self.env.ref('stock.view_picking_internal_search').id],
                'domain': [('is_expense', '!=', True)],
                'target': 'current',
            }
        super(Picking, self).sh_cancel()
        domain = [('is_expense', '=', True)]
        print("------------------ domain IS EXPANSE SET TO TRUE ??????")
        return {
            'name': 'Expense Transfers',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_type': 'form',
            'view_mode': 'list,kanban,form,calendar',
            'search_view_id': [self.env.ref('stock.view_picking_internal_search').id],
            'domain': domain,
            'target': 'current',
        }

class StockMove(models.Model):
    _inherit = "stock.move"

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        self.ensure_one()
        print("*********************************", self, self._context)
        AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

        move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        if move_lines:
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': description,
                'stock_move_id': self.id,
                'stock_valuation_layer_ids': [(6, None, [svl_id])],
                'move_type': 'entry',
            })
            new_account_move._post()

    def _get_accounting_data_for_valuation(self):
        """ Return the accounts and journal to use to post Journal Entries for
        the real-time valuation of the quant. """
        self.ensure_one()
        self = self.with_company(self.company_id)

        accounts_data = self.product_id.product_tmpl_id.with_context(is_expense=self.picking_id.is_expense, picking_id=self.picking_id).get_product_accounts()

        acc_src = self._get_src_account(accounts_data)
        acc_dest = self._get_dest_account(accounts_data)

        acc_valuation = accounts_data.get('stock_valuation', False)
        if acc_valuation:
            acc_valuation = acc_valuation.id
        if not accounts_data.get('stock_journal', False):
            raise UserError(_('You don\'t have any stock journal defined on your product category, check if you have installed a chart of accounts.'))
        if not acc_src:
            raise UserError(_('Cannot find a stock input account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (self.product_id.display_name))
        if not acc_dest:
            raise UserError(_('Cannot find a stock output account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (self.product_id.display_name))
        if not acc_valuation:
            raise UserError(_('You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))
        journal_id = accounts_data['stock_journal'].id
        return journal_id, acc_src, acc_dest, acc_valuation
