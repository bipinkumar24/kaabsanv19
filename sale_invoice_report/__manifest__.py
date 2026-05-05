# -*- encoding: utf-8 -*-
{
    'name': 'Sales invoice and Quotation report',
    'category': 'sales',
    'author': '',
    'license': 'OPL-1',
    'sequence': '10',
    'version': '19.0.1.0.0',
    'description': """
    Sales invoice and Quotation report
    """,
    'depends': [
        'sale', 'account'
    ],
    'data': [
        # 'report/sale_quotations_report.xml',
        'report/invoice_report.xml',
        'report/sale_quotations_reportnew.xml',
        'views/sale_invoice.xml',
    ],
    'installable': True,
    'application': True,
}
