# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'All in One Margin - Product, Sale, Invoice, POS Margin With Analysis',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'POS Margin on sales margin on invoice margin report analysis report sales margin product margin analysis report margin by percentage margin in invoice margin fix amount margin in SO margin point of sales margin on pos order margin apply margin on orders',
    'description' :"""
        This odoo app helps user to calculate maring for product in all application like sale order, customer invoice, point of sale order, User also can see margin on sale, invoice and pos order analysis report. Based on based on product sale price and cost price margin will calculated, also show percentage of margin for products. On order line when product selected then margin will also displayed.
    """,
    'author': 'BrowseInfo',
    'website': 'https://www.browseinfo.com',
    "price": 35,
    "currency": 'EUR',
    'depends': ['account', 'base', 'point_of_sale', 'product', 'sale_management', 'sale_margin'],
    'data': [
         'data/allow_margin_views.xml',
         'views/account_invoice_view.xml',
         'views/product_view.xml',
         'views/sale_view.xml',
         'views/pos_view.xml',
    ],
    'license':'OPL-1',
    'demo': [],
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://youtu.be/249TzaPH-60',
    "images":["static/description/Banner.gif"],
}
