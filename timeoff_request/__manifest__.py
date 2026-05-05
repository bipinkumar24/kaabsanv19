# -*- coding: utf-8 -*-
{
    'name': "timeoff_request",

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
    'category': 'Uncategorized',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_holidays'],


    # always loaded
    'data': [
        #'security/security.xml',
        'views/views.xml',
    ],
    'images': ['static/description/leave.png'],
    'installable': True,
    'application': True,
    # only loaded in demonstration mode
}
