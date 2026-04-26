# -*- coding: utf-8 -*-
{
    'name': "Manufacturing Orders Extended",
    'summary': """Manufacturing Orders Extended""",
    'description': """Manufacturing Orders Extended""",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'MRP',
    'version': '19.0.1.0.0',
    # Odoo 19 migration: manufacturing valuation account moves are provided by mrp_account.
    # Old dependency list kept for migration reference:
    # ['mrp', 'stock_account', 'bi_odoo_process_costing_manufacturing']
    'depends': ['mrp_account', 'bi_odoo_process_costing_manufacturing'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_production_view.xml',
        'wizard/change_date.xml',
    ],
}
