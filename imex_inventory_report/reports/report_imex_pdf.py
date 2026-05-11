# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
import calendar

class ReportImexPdf(models.AbstractModel):
    _name = 'report.imex_inventory_report.report_imex_pdf'
    _description = 'Report Invenory Template'

    @api.model
    def _get_report_values(self, docids, data=None):
        details = data.get('details')
        inventory_ids = self.env["imex.inventory.details.report"].browse(details)
        name = data.get('name')
        location_id = data.get('location_id')
        date_records = inventory_ids.filtered(lambda r: r.date)
        not_date_records = inventory_ids.filtered(lambda r: not r.date)
        sorted_records = date_records.sorted(key=lambda r: r.date)
        from_date = data.get('date_from')
        date_to = data.get('date_to')
        data = {
            'not_date_records' : not_date_records,
            'sorted_records': sorted_records,
            'name': name,
            'from_date': from_date,
            'date_to': date_to,
            'location_id': location_id
        }
        return data
