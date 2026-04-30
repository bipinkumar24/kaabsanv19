# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################
{
    'name': "Manufacturing Backdate (Forcedate)",
    'category': 'Manufacturing',
    'version': '19.0.1.0',
    'author': 'Equick ERP',
    'description': """
        This Module allows user to do mrp order in back dated/force dated.
        * Allow user to do mrp order in back dated-force dated.
        * Update the date in stock moves and product moves.
        * Update the date in stock valuation.
        * Update the date in journal entries if product have automated valuation method.
    """,
    'summary': """mrp backdated manufacturing order backdated mrp order backdated mrp forcedated manufacturing order force dated mo forcedate mrp order forcedate stock move backdate mrp order backdate manufacturing order backdate.""",
    'depends': ['mrp'],
    'price': 12,
    'currency': 'EUR',
    'license': 'OPL-1',
    'website': "",
    'data': [
        'views/mrp_product_produce_view.xml',
    ],
    'live_test_url': 'https://www.youtube.com/watch?v=Ay7uk3DDwRQ',
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
