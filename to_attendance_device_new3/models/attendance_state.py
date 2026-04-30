from odoo import models, fields, api


class AttendanceState(models.Model):
    _name = 'attendance.state'
    _inherit = 'mail.thread'
    _description = 'Attendance State'

    name = fields.Char(string='Name', help='The name of the attendance state. E.g. Login, Logout, Overtime Start, etc', required=True, translate=True,
                       tracking=True)
    activity_id = fields.Many2one('attendance.activity', string='Activity', required=True,
                                  help='Attendance activity, e.g. Normal Working, Overtime, etc', tracking=True)
    code = fields.Integer(string='Code Number', help='An integer to express the state code', required=True, tracking=True)
    type = fields.Selection([('checkin', 'Check-in'),
                            ('checkout', 'Check-out')], string='Activity Type', required=True, tracking=True)

    _sql_constraints = [
        ('code_unique',
         'UNIQUE(code)',
         "The Code must be unique!"),
        ('name_activity_id_unique',
         'UNIQUE(name, activity_id)',
         "The state name must be unique within the same activity!"),
        ('name_activity_id_unique',
         'UNIQUE(type, activity_id)',
         "The Activity Type and Activity must be unique! Please recheck if you have previously defined an attendance status with the same Activity Type and Activity"),
    ]

    def _compute_display_name(self):
        for r in self:
            r.display_name = '[' + (r.activity_id.name or '') + '] ' + (r.name or '')

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        domain = domain or []
        search_domain = []
        if name:
            search_domain = ['|', ('activity_id.name', '=ilike', name + '%'), ('name', operator, name)]
        records = self.search(search_domain + domain, limit=limit)
        return [(r.id, r.display_name) for r in records]

