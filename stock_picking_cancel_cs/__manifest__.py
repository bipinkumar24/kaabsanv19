# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Cancel Stock Picking (Delivery Order) & Reset to Draft",
    "version": "19.0.1.0.0",
    "author": "Craftsync Technologies",
    "category": "Inventory",
    "maintainer": "Craftsync Technologies",
    "summary": "Cancel done pickings and reset cancelled pickings back to draft.",
    "website": "https://www.craftsync.com/",
    "license": "OPL-1",
    "support": "info@craftsync.com",
    "depends": ["sale_management", "purchase", "sale_stock"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/stock_picking.xml",
        "views/view_sale_order.xml",
        "views/view_purchase_order.xml",
        "views/res_config_settings_views.xml",
        "wizard/view_cancel_delivery_wizard.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "images": ["static/description/main_screen.png"],
    "price": 9.99,
    "currency": "EUR",
}
