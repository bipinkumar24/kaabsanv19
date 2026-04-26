# -*- coding: utf-8 -*-
{
    'name': "validate_invoice",

    'summary': """ this module adds prepost stage before posting payments and journals""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Salam Smart Solutions",
    'website': "http://www.salamsmartsolutions.com",

    'category': 'Uncategorized',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',

    'depends': ['base', 'account'],

    # always loaded
    'data': [
        'views/account_view.xml',
    ],
    'installable': True,
    'application': False,
    #    ],
}
