# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Inventory Force Date",
    "summary": """
        Force the inventory adjustment and stock transfer date.
    """,
    "description": """
        Allow authorized users to set a forced inventory date on inventory
        adjustments and stock pickings so generated stock moves keep the
        chosen effective date.
""",
    "version": "19.0.1.0.0",
    "category": "Inventory",
    "sequence": 1,
    "author": "Eng-Mahmoud Ramadan",
    "website": "mailto:mramadan271193@gmail.com",
    "depends": [
        "base",
        "stock",
    ],
    "data": [
        "security/group.xml",
        "views/stock_quant.xml",
        "views/stock_picking.xml",
    ],
    "installable": True,
    "auto_install": False,
    "images": ["static/description/icon.png"],
    "price": 20,
    "currency": "EUR",
}
