# -*- coding: utf-8 -*-
{
    'name': "Sale Order Multi Warehouse",
    'summary': """Make deliveries for product quantity available on different warehouse for a sale order""",
    'description': """In the Odoo default Sales module you can only select a single warehouse, that means in some 
        cases when you have a product's quantity fully not available in one warehouse, so to deal with this case in 
        default odoo you need to create to different sales order from different warehouses to get the required quantity. 
        Lets understand the scenario with an example: Lets assume we have two warehouses, warehouse "A" and warehouse 
        "B". "Office Chair" quantity in the warehouse "A" is 30 and in warehouse "B" is 40. So overall we have 70 units 
        of "Office Chair" in our stock. But here the warehouses are different. Therefore, by using the Odoo default sales 
        module we can not order 50 units of "Office Chair" in the same sale order. Because it only allows you to use one 
        warehouse at a time.But, If we use Sale Order Multi Warehouse module, it will allow you to complete the required 
        quantity of a product from multiple warehouses. So now we can pick 30 units of "Office Chair" from warehouse "A" 
        and 20 units from warehouse "B". One more thing, No need to create multiple order lines for the same product. 
        After setting the quantities when we confirm the order it will group the order lines and create different 
        deliveries for different warehouses. Here in our e.g. it will create 2 deliveries, one for warehouse "A" and 
        other for warehouse "B".So it will be very convenient to manage deliveries for multiple warehouses.""",
    'author': "Bipin Prajapati",
    'category': 'Sales',
    'version': '19.0.0.1',
    'depends': ['sale_stock', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'OPL-1',
    'images': ['static/description/banner.jpg'],
    'price': 20,
    'currency': 'EUR',
}
