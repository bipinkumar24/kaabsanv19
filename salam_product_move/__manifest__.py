#-*- coding:utf-8 -*-
{
    'name': 'Custom Salam Product Move',
    'category': 'Stock',
    'version': '19.0.1.0.0',
    'author': 'Bipin Prajapati',
    'summary': 'Custom Salam Product Move',
    'description': "",
    'depends': [
        'sale_management', 'account','stock', 'stock_account', 'mrp'
    ],
    'data': [
        'views/stock_move.xml',
        'data/cron.xml'
    ],
}
