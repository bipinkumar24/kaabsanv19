{
    'name': 'HR Equipment ALL in ONE',
    'version': '19.0.1.0.0',
    'category': 'Generic Modules/Human Resources',
    'summary': """ 
            Equipment allocation and return or transfer to employees and equipment maintenance process includes following features
            Create allocation request and link equipment with product and serial
            Equipment request approvals
            Allocation and return or transfer
            Create Equipment Maintenance
            Add multiple components and create stock movements
            Create invoices for Maintenance
            Auto create Maintenance request based on define recurring days
            Skip request on employee weekend or holidays
            Equipment Maintenance
            Repair Maintenance
            Vehicle Maintenance
            Maintenance request 
            Auto Maintenance request 
            HR Equipment
            Repair Order
            Maintenance Request
            Equipment Allocation
            Employee Equipment allocation
        """,

    'depends': ['purchase_stock', 'hr_maintenance', 'account', 'project_timesheet_holidays'],
    'author': 'Preciseways',
    'data': [
        'data/data.xml',
        'data/email_data.xml',
        'security/ir.model.access.csv',
        'wizard/transfer_view.xml',
        'views/maintenance_request_views.xml',
        'views/recurring_work_schedule_view.xml',
        'views/allocation_request.xml',
        'views/checklist_line.xml',
        'views/product_inherit.xml',
    ],
    'installable': True,
    'application': True,
    'price': 31.0,
    'currency': 'EUR',
    'images':['static/description/banner.png'],
    'license': 'OPL-1',
}
