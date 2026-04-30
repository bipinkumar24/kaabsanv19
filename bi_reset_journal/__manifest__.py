# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    "name": "Reset Journal Entry | Cancel Journal Entry and Reset to Draft",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "summary": "Reset posted journal entries to draft and cancel single or multiple journal entries.",
    "description": """
        Reset to Draft Journal Entry Odoo App helps users set single or multiple
        journal entries back to draft so required changes can be made. Users can
        also cancel single or multiple journal entries in one click.
    """,
    "author": "BrowseInfo",
    "website": "https://www.browseinfo.com",
    "license": "OPL-1",
    "depends": ["base", "account"],
    "data": [
        "wizard/invoice_view.xml",
    ],
    "installable": True,
    "auto_install": False,
    "live_test_url": "https://youtu.be/q4p9HGRo5tY",
    "images": ["static/description/Reset-Journal-Entry-Banner.gif"],
    "price": 15,
    "currency": "EUR",
}
