# -*- coding: utf-8 -*-
{
    "name": "Inventory Onhand Report",
    "version": "19.0.1.0.0",
    "author": "Omega System",
    "maintainer": "Omega System",
    "website": "https://omegasystem.in/",
    "license": "AGPL-3",
    "category": "Inventory",
    "summary": "Stock on-hand report by location, product, and category.",
    "depends": [
        "sale",
        "stock",
        "stock_account",
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/onhand_wizard_view.xml",
        # Odoo 19 removed stock.valuation.layer; legacy valuation actions are disabled.
        # "views/stock_valuation_layer_view.xml",
        "wizard/journal_entery_wizard_view.xml",
        "wizard/report.xml",
    ],
    "images": ["static/description/banner.gif"],
    "price": 12.00,
    "currency": "EUR",
    "installable": True,
    "application": False,
    "auto_install": False,
}
