# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Manufacture Order Force Date",
    "summary": """
        Force the manufacturing order effective date.
    """,
    "description": """
        Allow authorized users to set a forced date on manufacturing orders so
        related stock moves and move lines keep the selected effective date.
    """,
    "version": "19.0.1.0.0",
    "category": "Manufacturing",
    "sequence": 1,
    "author": "Eng-Mahmoud Ramadan",
    "website": "mailto:mramadan271193@gmail.com",
    "depends": [
        "base",
        "stock",
        "mrp",
        "inventory_force_date",
    ],
    "data": [
        "views/mrp_production.xml",
    ],
    "installable": True,
    "auto_install": False,
    "images": ["static/description/icon.png"],
    "price": 5.0,
    "currency": "EUR",
}
