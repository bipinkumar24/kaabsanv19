# -*- coding: utf-8 -*-
{
    'name': "Manufacturing Orders Extended",
    'summary': """Manufacturing Orders Extended""",
    'description': """Manufacturing Orders Extended""",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'MRP',
    'version': '19.0.0.1',
    'depends': ['mrp','stock','stock_account'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_production_view.xml',
        'wizard/change_date.xml',

    ],
}
