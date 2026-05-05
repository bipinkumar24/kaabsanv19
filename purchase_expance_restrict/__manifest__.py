{
    'name': 'Purchase Request Expense Restrict',
    'version': '19.0.1.0.0',
    'summary': 'Restrict expense_create on purchase request lines based on Not Storable flag.',
    'depends': ['atta_purchase_request'],
    'data': [
        'views/purchase_request_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
