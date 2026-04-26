from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_repr
from odoo.exceptions import ValidationError
from collections import defaultdict


class Product(models.Model):
    _inherit = 'product.product'

    old_categ_id = fields.Many2one('product.category', 'Product Old Category')


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'


    def _get_product_accounts(self):
        """ Add the stock accounts related to product to the result of super()
        @return: dictionary which contains information regarding stock accounts and super (income+expense accounts)
        """
        accounts = super(ProductTemplate, self)._get_product_accounts()
        ctx = self._context
        if ctx.get('is_expense'):
            picking_id = ctx.get('picking_id')
            if picking_id.property_valuation == 'real_time':
                accounts.update({
                    # 'stock_input': picking_id.property_stock_account_input_categ_id,
                    'stock_output': picking_id.property_stock_account_output_categ_id,
                    # 'stock_valuation': picking_id.property_stock_valuation_account_id,
                })
        return accounts

    # def get_product_accounts(self, fiscal_pos=None):
    #     """ Add the stock journal related to product to the result of super()
    #     @return: dictionary which contains all needed information regarding stock accounts and journal and super (income+expense accounts)
    #     """
    #     ctx = self._context
    #     accounts = super(ProductTemplate, self).get_product_accounts(fiscal_pos=fiscal_pos)
    #     accounts.update({'stock_journal': self.categ_id.property_stock_journal or False})
    #     if ctx.get('is_expense'):
    #         picking_id = ctx.get('picking_id')
    #         if picking_id.property_valuation == 'real_time':
    #             accounts.update({'stock_journal': picking_id.property_stock_journal})
    #     return accounts