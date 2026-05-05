# -*- coding: utf-8 -*-
{
    'name': 'Change Effective Date on Stock App',
    "author": "Edge Technologies",
    'version': '19.0.1.0',
    'live_test_url': "https://youtu.be/WPR1PCyCU48",
    "images":['static/description/main_screenshot.png'],
    'summary':'Stock Change Effective Date in stock backdate stock back date stock force date on stock picking change effective date inventory effective date change on stock picking effective date change inventory backdate inventory back date picking backdate in stock',
    'description': """
    Change Effective Date : Changes The Effective Date In Stock Picking And It Stock Move, Inventory Valuation And Journal Entry With Single Or Multiple Picking
""",
    "license" : "OPL-1",
    'depends': ['stock', 'account'],
    'data': [
            'security/security.xml',
            'security/ir.model.access.csv',
            'views/stock_picking_inherited_view.xml',
            'wizard/change_effective_date_wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'price': 25,
    'currency': "EUR",
    'category': 'Warehouse',
}
