# -*- coding: utf-8 -*-
{
    'name': 'Cancel Manufacturing Order | Cancel MRP Order',
    "author": "Edge Technologies",
    'version': '19.0.1.0',
    'description': """ 
        Cancel confirmed manufacturing order app
    """,
    "summary" : 'Manufacturing order cancel manufacturing reset to draft manufacturing order cancel MRP cancel MRP reset to draft MRP  order cancel order cancel and reset to draft manufacturing production order cancel production order cancel MO cancel and reset to draft MO.',
    'live_test_url': "https://youtu.be/ErGBvXKh9h0",
    "images":["static/description/main_screenshot.png"],
    "license" : "OPL-1",
    'depends' : ['mrp', 'account'],
    'data': [
        'security/security.xml',
        'views/manufacturing_order_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'price': 15,
    'currency': "EUR",
    'category': 'Manufacturing',
}
