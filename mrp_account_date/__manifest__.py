# -*- coding: utf-8 -*-
{
    'name': "MRP Accounting Date",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Manufacturing',
    'version': '19.0.1.0.0',

    # any module necessary for this one to work correctly
    # Odoo 19 migration: stock valuation journal entries are provided by mrp_account/stock_account.
    # Old dependency kept for migration reference: ['mrp']
    'depends': ['mrp_account'],

    # always loaded
    'data': [
        'views/mrp_inherit_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
