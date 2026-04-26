#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Custom Salam CRM',
    'category': 'CRM',
    'version': '19.0.1.0.0',
    'author': 'Bipin Prajapati',
    'summary': 'Custom Salam CRM',
    'description': "",
    'depends': [
        'sale_management', 'account', 'crm', 'car_reservation'
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/remark_view.xml',
        'views/approval_level_crm_view.xml',
        'views/crm_lead_view.xml',
    ],
}
