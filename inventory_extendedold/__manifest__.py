# -*- coding: utf-8 -*-
{
   "name": "Inventory Extended",
   "summary": """Inventory Extended""",
   "description": """Inventory Extended""",
   "category": "Inventory",
   "version": "19.0.0",
   "license": "OPL-1",
   "depends": ['stock','atta_purchase_request','fleet'],
   "data": [
      "security/ir.model.access.csv",
      "security/access_group.xml",
      "views/stock_location_view.xml",
      "views/stock_scrap_view.xml",
    ],
    "installable": True,
    "application": True
}
