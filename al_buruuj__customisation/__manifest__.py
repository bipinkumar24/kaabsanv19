{
    'name': 'AlBuruuj Customisation',
    'version': '19.0.1.0.0',
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
    'depends': ['base', 'product', 'sale_management', 'account', 'purchase', 'purchase_stock', 'sale'],
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
