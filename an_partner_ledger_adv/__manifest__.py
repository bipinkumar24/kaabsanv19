{
    'name': 'Advanced Partner Ledger Report',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Print partner ledger report with invoice Details and Confirmation',
    'author': 'Ahmed Nour',
    'website': 'https://odoosa.net',
    'license': 'LGPL-3',
    'price': 60,
    'currency': 'USD',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/partner_ledger_wizard_views.xml',
        'report/partner_ledger_report.xml',
        'report/partner_ledger_templates.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'description': """
Advanced Partner Ledger Report
==============================

This module provides a comprehensive and customizable partner ledger report with multiple filtering options:

Key Features:
------------
* Custom Date Range - Generate reports for specific time periods
* Multiple Partner Selection - Choose individual partners, partner categories, or filter by salesperson
* Journal Filtering - Limit the report to specific journals
* Reconciliation Options - Include or exclude fully reconciled entries
* Invoice Details - Display detailed invoice line information including products, quantities, and prices
* Delivery Address - Show delivery address for sales and purchase transactions
* Salesperson Filtering - Filter results by specific salesperson
* Summary Reports - Generate summary reports grouped by salesperson
* Balance Confirmation - Include a professional balance confirmation section for client signature
* Arabic Balance Confirmation (مطابقة الرصيد) - Full Arabic language support with proper RTL formatting
* Multilingual Support - Full support for right-to-left languages including Arabic

For more information, please visit https://odoosa.net
"""
}
