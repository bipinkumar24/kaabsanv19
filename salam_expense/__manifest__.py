#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Salam Inventory Expense',
    'category': 'Sale',
    'version': '19.0.1.0.0',
    'author': 'Bipin Prajapati',
    'summary': 'Custom Salam Sale',
    'description': "",
    'license': 'AGPL-3',
    'depends': [
        'sale_management', 'account','stock', 'hr', 'stock_account', 'sh_all_in_one_cancel_adv',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/product_data.xml',
        'views/picking_view.xml',
        'wizard/remark_view.xml',
    ],
}
