# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import datetime
import calendar
from io import BytesIO


class InvenoryReportXlsx(models.AbstractModel):
    _name = 'report.imex_inventory_report.invenory_report_xlsx'
    _description = 'Inventory Report XLSX'
    # report_xlsx (OCA) not available in Odoo 19 — XLSX export disabled

    
    def generate_xlsx_report(self, workbook, data, obj):
        sheet = workbook.add_worksheet('Attendance_Info')

        format1 = workbook.add_format({'font_size': 10, 'align': 'center' , 'bold': True, 'bg_color': '#D3D3D3'})
        format2 = workbook.add_format({'font_size': 10, 'align': 'left' , 'bold': True})
        format3 = workbook.add_format({'font_size': 10, 'align': 'center'})
        format4 = workbook.add_format({'font_size': 10, 'align': 'top', 'bold': True})
        date_format_1 = workbook.add_format({'num_format': 'd-m-yyyy', 'font_size': 10, 'align': 'left' , 'bold': True})

        details = data.get('details')
        if details:
            inventory_ids = self.env["imex.inventory.details.report"].browse(details)
            date_records = inventory_ids.filtered(lambda r: r.date)
            not_date_records = inventory_ids.filtered(lambda r: not r.date)
            sorted_records = date_records.sorted(key=lambda r: r.date)
            main_record = not_date_records + sorted_records
            date_from = data.get('date_from')
            date_to = data.get('date_to')
            string = 'Imex Inventory report - -' + data.get('name')
            sheet.write('A1', string)
            sheet.write('A2', 'Date From', format1)
            if date_from:
                sheet.write('B2', date_from, format1)
            sheet.write('C2', 'Date To', format1)
            if date_to:
                sheet.write('D2', date_to, format1)
            sheet.write('E2', 'Location', format1)
            if data.get('location_id'):
                sheet.write('F2', '', format1)
            else:
                sheet.write('F2', 'All', format1)
            sheet.write('G2', 'Category', format1)
            if data.get('product_category_ids'):
                sheet.write('H2', '', format1)
            else:
                sheet.write('H2', 'All', format1)

            sheet.write('A4', 'Date', format1)
            sheet.write('B4', 'Reference', format1)
            sheet.write('C4', 'Partner', format1)
            sheet.write('D4', 'Source Location', format1)
            sheet.write('E4', 'Dest Location', format1)
            sheet.write('F4', 'Price', format1)
            sheet.write('G4', 'In', format1)
            sheet.write('H4', 'Out', format1)
            sheet.write('I4', 'Balance', format1)
            sheet.write('J4', 'Amount', format1)
            product_balance = not_date_records[0].initial if not_date_records else 0
            product_amount = not_date_records[0].initial if not_date_records else 0

            sheet.write(4, 1, 'initial', format2)
            sheet.write(4, 8, not_date_records[0].initial if not_date_records else 0, format2)
            sheet.write(4, 9, not_date_records[0].initial_amount if not_date_records else 0, format2)

            row = 5
            for line in sorted_records:
                column = 0
                product_balance = product_balance + line.product_in - line.product_out
                product_amount = product_amount + line.product_in * line.unit_cost - line.product_out * line.unit_cost

                sheet.write(row, column,  line.date, date_format_1)
                column += 1
                sheet.write(row, column,  line.display_name, format2)
                column += 1
                if line.picking_id and line.picking_id.partner_id:
                    sheet.write(row, column,  line.picking_id.partner_id.name, format2)
                    column += 1
                else:
                    sheet.write(row, column,  '', format2)
                    column += 1
                sheet.write(row, column,  line.location_id.complete_name, format2)
                column += 1
                sheet.write(row, column,  line.location_dest_id.complete_name, format2)
                column += 1
                sheet.write(row, column,  line.unit_cost, format2)
                column += 1
                sheet.write(row, column,  line.product_in, format2)
                column += 1
                sheet.write(row, column,  line.product_out, format2)
                column += 1
                sheet.write(row, column,  product_balance, format2)
                column += 1
                sheet.write(row, column,  product_amount, format2)
                column += 1
                row += 1

