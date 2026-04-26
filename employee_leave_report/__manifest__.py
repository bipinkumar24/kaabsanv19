# -*- coding: utf-8 -*-
{
    'name': "Employee Leave Report",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    'category': 'Human Resources/Time Off',
    'version': '19.0.1.0.0',

    'depends': ['base', 'hr_holidays'],

    'data': [
        'security/ir.model.access.csv',
        'wizard/employee_leave_report.xml',
        'wizard/leave_report_wizard_view.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/leave_report_template.xml',
    ],
    'installable': True,
    'application': True,
}
