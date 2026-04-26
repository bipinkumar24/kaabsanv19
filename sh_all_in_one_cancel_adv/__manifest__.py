# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
{
    "name": "All In One Cancel - Advance | Cancel Sale Orders | Cancel Purchase Ordrs | Cancel Invoices | Cancel Invenory | Cancel Manufacturing Orders | Cancel Point Of Sale Orders | Cancel Landed Costs | Canel HR Expenses",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Extra Tools",
    "license": "OPL-1",
    "summary": "Sale Order Cancel, Delete Quotation, Purchase Order Delete, Request For Quotation Delete, Cancel POS, Cancel MRP,Delete Invoice, Cancel Payment, Cancel Inventory Adjustment, Cancel Internal Transfer,Cancel Stock Moves Odoo",
    "description": """This module helps to cancel sale orders, purchase orders, invoices, payments, inventory (inventory transfer, inventory adjustment, stock move & scrap Orders), manufacturing orders, landed costs, HR Expenses, point of sale orders. You can also cancel multiple records from the tree view.""",
    "version": "19.0.1",
    "depends": [

              "account", "purchase", "sale_management", "stock", "point_of_sale",
             #"account", "purchase", "sale_management", "stock", "hr_expense", "stock_landed_costs", "mrp", "point_of_sale",
    ],
    "application": True,
    "data": [

        # "sh_account_cancel/security/account_security.xml",
        # "sh_account_cancel/data/data.xml",
        # "sh_account_cancel/views/res_config_settings.xml",
        # "sh_account_cancel/views/views.xml",


        # 'sh_purchase_cancel/security/purchase_security.xml',
        # 'sh_purchase_cancel/data/data.xml',
        # 'sh_purchase_cancel/views/purchase_config_settings.xml',
        # 'sh_purchase_cancel/views/views.xml',


        # 'sh_sale_cancel/security/sale_security.xml',
        # 'sh_sale_cancel/data/data.xml',
        # 'sh_sale_cancel/views/sale_config_settings.xml',
        # 'sh_sale_cancel/views/views.xml',


        'sh_stock_cancel/security/stock_security.xml',
        'sh_stock_cancel/data/data.xml',
        'sh_stock_cancel/views/res_config_settings.xml',
        'sh_stock_cancel/views/views.xml',


        #'sh_hr_expense_cancel/security/hr_security.xml',
        #'sh_hr_expense_cancel/data/data.xml',
        #'sh_hr_expense_cancel/views/hr_config_settings.xml',
        #'sh_hr_expense_cancel/views/views.xml',


        #'sh_landed_cost_cancel/security/landed_cost_security.xml',
        #'sh_landed_cost_cancel/data/data.xml',
        #'sh_landed_cost_cancel/views/stock_config_settings.xml',
        #'sh_landed_cost_cancel/views/views.xml',


        #'sh_mrp_cancel/security/mrp_security.xml',
        #'sh_mrp_cancel/data/data.xml',
        #'sh_mrp_cancel/views/mrp_config_settings.xml',
        #'sh_mrp_cancel/views/views.xml',


        # 'sh_pos_cancel/security/pos_security.xml',
        # 'sh_pos_cancel/data/data.xml',
        # 'sh_pos_cancel/views/pos_config_settings.xml',
        # 'sh_pos_cancel/views/views.xml',


    ],

    "images": ['static/description/background.png', ],
    "auto_install": False,
    "installable": True,
    "price": "120",
    "currency": "EUR"
}
