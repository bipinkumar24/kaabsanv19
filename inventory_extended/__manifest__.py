# -*- coding: utf-8 -*-
{
   "name": "Inventory Extended",
   "summary": """
       Inventory Extended""",
   "description": """
       Inventory Extended""",

   "category": "Inventory",
   'author': 'Do Incredible',
   "version": "19.0.0.1",
   "license": "OPL-1",
   "depends": ['stock','atta_purchase_request'],
   "data": [
        "security/access_group.xml",
        "views/stock_location_view.xml",
        "views/stock_scrap_view.xml",
   ],
   "installable": True,
   
   "application": True
}
