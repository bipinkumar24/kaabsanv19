from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime, timedelta


class MaintenanceChecklistLine(models.Model):
    _name = 'maintenance.checklist.line'
    _description = 'Maintenance Checklist Line'


    checklist_ids = fields.Char(required=True, string='Title/Name')
    descriptione = fields.Text(required=True, string='Discription')
    request_id = fields.Many2one('maintenance.request', string="Maintenance Request", ondelete='cascade')
    equipment_id = fields.Many2one('maintenance.equipment')

class DamageDtailsLine(models.Model):
    _name = 'damage.details.line'
    _description = 'Maintenance Checklist Line'


    date = fields.Date()
    descriptione = fields.Char(string='Discription')
    request_id = fields.Many2one('maintenance.request', string="Maintenance Request", ondelete='cascade')
    allocation_id = fields.Many2one('allcation.request', ondelete='cascade')
