# -*- coding: utf-8 -*-
{
    "name": "Manufacturing Reset Bom Cost Extended",
    "summary": "Refresh BOM cost before completing manufacturing orders and fix valuation layers.",
    "description": """
        Recompute BOM-based product costs when completing manufacturing orders
        and provide a stock valuation layer action to correct inconsistent
        valuation amounts from related journal entries.
    """,
    "author": "My Company",
    "website": "http://www.yourcompany.com",
    "category": "Manufacturing",
    "version": "19.0.1.0.0",
    "depends": ["mrp", "stock_account"],
    "data": [
        # Odoo 19 removed stock.valuation.layer; legacy valuation actions are disabled.
        # "views/stock_valuation_layer_view.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
}
