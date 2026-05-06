{
    'name': 'Effective Date Change Scrap',
    'version': '19.0.1.0.0',
    'summary': 'Change effective date of scrap order and its related journal entry',
    'category': 'Inventory',
    'author': 'Kaabsan',
    'depends': ['stock', 'stock_account'],
    'data': [
        'security/ir.model.access.csv',
        'views/change_scrap_date_wizard_view.xml',
        'views/stock_scrap_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
