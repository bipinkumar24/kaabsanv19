# -*- coding: utf-8 -*-
{
    'name': 'AlBuruuj Customisation',
    'version': '14.0.0.1.0',
    'category': 'Sales',
    'summary': 'AlBuruuj Customisation',
    'description': """
        This module add extra stage to sale process for groups
        * Sales
        * MRP
        * Admin
        * MAINTENANCE
    """,
    'sequence': 1,
    'author': 'Ahmed Abdi',
    'website': 'https://alburuujgroup.com/',
    'depends': ['base','sale_management', 'account','purchase','purchase_stock'],
    'data': [
        'data/mail_template.xml',
        'wizard/sale_approval_reason_view.xml',
        'views/views.xml',
        'reports/payment_report_inherit.xml',
        'security/ir.model.access.csv',
        
    ],
    'images': [
        'static/description/AlbGroup.png',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3'
}
