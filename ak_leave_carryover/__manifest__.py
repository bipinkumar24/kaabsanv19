{
    'name': "Time Off Carry Over",   
    'summary': "Manage staff time off carry over",   
    'description': """
        Easily manage and schedule your staff's time off carry-over with this app.
    """,   
    'author': "Abdullah Khalil",
    'category': 'Time Off',
    'version': '19.0.1.0.0',
    'depends': ['base', 'hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'views/carryover_views.xml',
        'views/hr_leave_allocation_views.xml',
    ],
    'images': ["static/description/banner.png"],
    'license': 'LGPL-3',
    'application': True,
    'installable': True,
}
