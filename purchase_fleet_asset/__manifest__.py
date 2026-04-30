# -*- coding: utf-8 -*-
{
    'name': 'Purchase – Fleet & Asset Tagging',
    'version': '19.0.1.0.0',
    'category': 'Purchase',
    'summary': 'Tag each purchase line to a Fleet Vehicle OR Asset (single column)',
    'depends': ['purchase', 'fleet', 'account_asset', 'extend_asset'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
        'views/purchase_report_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
