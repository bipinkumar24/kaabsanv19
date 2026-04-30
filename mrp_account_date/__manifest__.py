# -*- coding: utf-8 -*-
{
    'name': "MRP Account Date",
    'summary': "Adds accounting date functionality to Manufacturing Orders",
    'description': """
        This module extends the Manufacturing (MRP) module
        to manage and control accounting dates related to
        manufacturing operations.

        It allows better financial tracking and alignment
        between production and accounting entries.
    """,
    'author': "Bipin Prajapati",
    'website': "",
    'category': 'Manufacturing',
    'version': '19.0.1.0.0',  # Change according to your Odoo version
    'depends': ['mrp','account'],
    'data': [
        'views/mrp_inherit_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
