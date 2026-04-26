# -*- coding: utf-8 -*-
{
    'name': "inherit_car",

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
    'category': 'Services',
    'version': '19.0.1.0.0',

    # any module necessary for this one to work correctly
    # Odoo 19 migration: car.reservation is provided by the custom car_reservation module.
    # Old dependency list kept for migration reference: ['base', 'crm']
    'depends': ['base', 'crm', 'car_reservation'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/car_inherit_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
