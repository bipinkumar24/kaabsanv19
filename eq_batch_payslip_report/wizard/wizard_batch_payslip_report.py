# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

import xlsxwriter
import base64
from odoo import fields, models, api, _

class HRSalaryRuleCategory(models.Model):
    _inherit = 'hr.salary.rule.category'

    is_cnss = fields.Boolean('Print CNSS Report?')
    sequence_cnss = fields.Integer('Sequence CNSS Report')
    sequence_batch = fields.Integer('Sequence Of Batch Payslip')


class wizard_batch_payslip_report(models.TransientModel):
    _name = 'wizard.batch.payslip.report'
    _description = 'Wizard Batch Payslip Report'

    xls_file = fields.Binary(string='Download')
    name = fields.Char(string='File name', size=64)
    state = fields.Selection([('choose', 'choose'),
                              ('download', 'download')], default="choose", string="Status")
    batch_id = fields.Many2one('hr.payslip.run', string="Batch Ref.", default=lambda self: self._context.get('active_id'))
    hr_payroll_structure_id = fields.Many2one('hr.payroll.structure', 'Salary Structure')

    def print_report_xls(self):

        if self.env.context.get('type') == 'batch':
            batch_id = self.batch_id
            xls_filename = 'Batch Payslip Report.xlsx'
            workbook = xlsxwriter.Workbook('/tmp/' + xls_filename)
            worksheet = workbook.add_worksheet("Batch Payslip Report")

            text_center = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
            text_center.set_text_wrap()
            font_bold_center = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
            font_bold_right = workbook.add_format({'bold': True, 'align': 'right'})
            font_bold_right.set_num_format('###0.00')
            number_format = workbook.add_format()
            number_format.set_num_format('###0.00')
            font_right = workbook.add_format({'align': 'right'})

            worksheet.set_column('A:AZ', 18)
            for i in range(3):
                worksheet.set_row(i, 18)
            worksheet.write(0, 1, 'Company Name', font_bold_center)
            worksheet.merge_range(0, 2, 0, 3, self.env.user.company_id.name or '', text_center)
            worksheet.write(1, 1, 'Batch Name', font_bold_center)
            worksheet.merge_range(1, 2, 1, 3, batch_id.name or '', text_center)
            worksheet.write(2, 1, 'Period', font_bold_center)
            worksheet.merge_range(2, 2, 2, 3, str(batch_id.date_start) + ' - ' + str(batch_id.date_end), text_center)
            row = 5
            worksheet.merge_range(row, 0, row + 1, 0, 'No #', font_bold_center)
            worksheet.merge_range(row, 1, row + 1, 1, 'Payslip Ref', font_bold_center)
            worksheet.merge_range(row, 2, row + 1, 2, 'EmpID', font_bold_right)
            worksheet.merge_range(row, 3, row + 1, 3, 'Employee', font_bold_center)
            worksheet.merge_range(row, 4, row + 1, 4, 'Mobile', font_bold_right)
            worksheet.merge_range(row, 5, row + 1, 5, 'Bank Acc', font_bold_right)
            worksheet.merge_range(row, 6, row + 1, 6, 'Designation', font_bold_center)

            col = 7
            worksheet.set_row(row + 1, 30)
            result = self.get_header(batch_id)
            col_lst = []
            # make the header by category
            for item in result:
                for categ_id, salary_rule_ids in item.items():
                    if not salary_rule_ids:
                        continue
                    if len(salary_rule_ids) == 1:
                        worksheet.write(row, col, categ_id.name, font_bold_center)
                        worksheet.write(row + 1, col, salary_rule_ids[0].name, text_center)
                        col += 1
                        col_lst.append(salary_rule_ids[0])
                    else:
                        rule_count = len(salary_rule_ids) - 1
                        worksheet.merge_range(row, col, row, col + rule_count, categ_id.name, font_bold_center)
                        for rule_id in salary_rule_ids.sorted(key=lambda l: l.sequence):
                            worksheet.write(row + 1, col, rule_id.name, text_center)
                            col += 1
                            col_lst.append(rule_id)
            row += 3
            sr_no = 1
            total_rule_sum_dict = {}
            # print the data of payslip
            for payslip in batch_id.mapped('slip_ids'):
                worksheet.write(row, 0, sr_no, text_center)
                # worksheet.write(row, 1, payslip.employee_reference)
                worksheet.write(row, 2, payslip.employee_id.identification_id or '', font_right)
                worksheet.write(row, 3, payslip.employee_id.name)
                worksheet.write(row, 4, payslip.employee_id.work_phone, font_right)
                active_bank = self.env['res.partner.bank'].search([
                    ('id', 'in', payslip.employee_id.bank_account_ids.ids),
                    ('active', '=', True)], limit=1)
                name = active_bank.acc_number or ''
                worksheet.write(row, 5, name, font_right)
                worksheet.write(row, 6, payslip.employee_id.job_id.name or '')
                col = 7
                for col_rule_id in col_lst:
                    line_id = payslip.line_ids.filtered(lambda l: l.salary_rule_id.code == col_rule_id.code)
                    amount = line_id.total or 0.0
                    worksheet.write(row, col, amount, number_format)
                    col += 1
                    total_rule_sum_dict.setdefault(col_rule_id, [])
                    total_rule_sum_dict[col_rule_id].append(amount)
                row += 1
                sr_no += 1
            # print the footer
            col = 7
            row += 1
            worksheet.write(row, 6, "Total", font_bold_center)
            for col_rule_id in col_lst:
                worksheet.write(row, col, sum(total_rule_sum_dict.get(col_rule_id, [])), font_bold_right)
                col += 1
            workbook.close()
            action = self.env.ref('eq_batch_payslip_report.action_wizard_batch_payslip_report').read()[0]
            action['res_id'] = self.id
            self.write({'state': 'download',
                        'name': xls_filename,
                        'xls_file': base64.b64encode(open('/tmp/' + xls_filename, 'rb').read())})
            return action
        else:
            batch_id = self.batch_id
            xls_filename = 'CNSS Payslip Report.xlsx'
            workbook = xlsxwriter.Workbook('/tmp/' + xls_filename)
            worksheet = workbook.add_worksheet("CNSS Payslip Report")

            text_center = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
            text_center.set_text_wrap()
            font_bold_center = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
            font_bold_right = workbook.add_format({'bold': True, 'align': 'right'})
            font_bold_right.set_num_format('###0.00')
            number_format = workbook.add_format()
            number_format.set_num_format('###0.00')
            font_right = workbook.add_format({'align': 'right'})

            worksheet.set_column('A:AZ', 18)
            for i in range(3):
                worksheet.set_row(i, 18)
            worksheet.write(0, 1, 'Company Name', font_bold_center)
            worksheet.merge_range(0, 2, 0, 3, self.env.user.company_id.name or '', text_center)
            # worksheet.write(1, 1, 'Batch Name', font_bold_center)
            worksheet.merge_range(1, 2, 1, 3, batch_id.name or '', text_center)
            worksheet.write(2, 1, 'Period', font_bold_center)
            worksheet.merge_range(2, 2, 2, 3, str(batch_id.date_start) + ' - ' + str(batch_id.date_end), text_center)
            row = 5
            worksheet.merge_range(row, 0, row + 1, 0, 'No #', font_bold_center)
            # worksheet.merge_range(row, 1, row + 1, 1, 'Payslip Ref', font_bold_center)
            worksheet.merge_range(row, 1, row + 1, 1, 'EmpID', font_bold_right)
            worksheet.merge_range(row, 2, row + 1, 2, 'Employee', font_bold_center)
            # worksheet.merge_range(row, 4, row + 1, 4, 'Mobile', font_bold_right)
            # worksheet.merge_range(row, 5, row + 1, 5, 'Bank Acc', font_bold_right)
            worksheet.merge_range(row, 3, row + 1, 3, 'Designation', font_bold_center)

            col = 4
            worksheet.set_row(row + 1, 30)
            result = self.get_header(batch_id)
            col_lst = []
            # make the header by category
            for item in result:
                for categ_id, salary_rule_ids in item.items():
                    if not salary_rule_ids:
                        continue
                    if len(salary_rule_ids) == 1:
                        worksheet.write(row, col, categ_id.name, font_bold_center)
                        worksheet.write(row + 1, col, salary_rule_ids[0].name, text_center)
                        col += 1
                        col_lst.append(salary_rule_ids[0])
                    else:
                        rule_count = len(salary_rule_ids) - 1
                        worksheet.merge_range(row, col, row, col + rule_count, categ_id.name, font_bold_center)
                        for rule_id in salary_rule_ids.sorted(key=lambda l: l.sequence):
                            worksheet.write(row + 1, col, rule_id.name, text_center)
                            col += 1
                            col_lst.append(rule_id)
            row += 3
            sr_no = 1
            total_rule_sum_dict = {}
            # print the data of payslip
            for payslip in batch_id.mapped('slip_ids'):
                going_deep = False
                for col_rule_id in col_lst:
                    line_id = payslip.line_ids.filtered(lambda l: l.salary_rule_id.code == col_rule_id.code)
                    amount = line_id.total or 0.0
                    if col_rule_id.code != 'NET' and amount > 0:
                        going_deep = True
                if going_deep:
                    if payslip.struct_id.id == self.hr_payroll_structure_id.id:
                        worksheet.write(row, 0, sr_no, text_center)
                        # worksheet.write(row, 1, payslip.employee_reference)
                        worksheet.write(row, 1, payslip.employee_id.identification_id or '', font_right)
                        worksheet.write(row, 2, payslip.employee_id.name)
                        # worksheet.write(row, 4, payslip.employee_id.work_phone, font_right)
                        active_bank = self.env['res.partner.bank'].search([
                            ('id', 'in', payslip.employee_id.bank_account_ids.ids),
                            ('active', '=', True)], limit=1)
                        name = active_bank.acc_number or ''
                        worksheet.write(row, 5, name, font_right)
                        worksheet.write(row, 3, payslip.employee_id.job_id.name or '')
                        col = 4
                        for col_rule_id in col_lst:
                            line_id = payslip.line_ids.filtered(lambda l: l.salary_rule_id.code == col_rule_id.code)
                            amount = line_id.total or 0.0
                            worksheet.write(row, col, amount, number_format)
                            col += 1
                            total_rule_sum_dict.setdefault(col_rule_id, [])
                            total_rule_sum_dict[col_rule_id].append(amount)
                        row += 1
                        sr_no += 1
            # print the footer
            col = 4
            row += 1
            worksheet.write(row, 6, "Total", font_bold_center)
            for col_rule_id in col_lst:
                worksheet.write(row, col, sum(total_rule_sum_dict.get(col_rule_id, [])), font_bold_right)
                col += 1
            workbook.close()
            action = self.env.ref('eq_batch_payslip_report.action_wizard_batch_payslip_report').read()[0]
            action['res_id'] = self.id
            self.write({'state': 'download',
                        'name': xls_filename,
                        'xls_file': base64.b64encode(open('/tmp/' + xls_filename, 'rb').read())})
            return action


    def print_report_pdf(self):
        data = self.read()[0]
        return self.env.ref('eq_batch_payslip_report.action_print_batch_payslip').report_action([], data=data)

    def get_header(self, batch_id):
        if self.env.context.get('type') == 'batch':
            sorted_category_list_ids = self.env['hr.salary.rule.category'].search([
                ('code', 'in', ['BASIC', 'add', 'GROSS', 'DED', 'NET'])
            ])
            category_list_ids = sorted_category_list_ids.sorted(key=lambda c: c.sequence_batch)
        else:
            category_list_ids = self.env['hr.salary.rule.category'].search([('is_cnss', '=', True)], order='sequence_cnss')
        # find all the rule by category
        col_by_category = {}
        for payslip in batch_id.slip_ids:
            for line in payslip.line_ids:
                col_by_category.setdefault(line.category_id, [])
                col_by_category[line.category_id] += line.salary_rule_id.ids
        for categ_id, rule_ids in col_by_category.items():
            data_ids = self.env['hr.salary.rule'].browse(set(rule_ids))
            code = data_ids.mapped('code')
            data_set = []
            for co in code:
                rule_filter_ids = data_ids.filtered(lambda x:x.code == co and x.code != 'IDN')
                if rule_filter_ids:
                    data_set.append(rule_filter_ids[0].id)
            col_by_category[categ_id] = self.env['hr.salary.rule'].browse(set(data_set))
        # make the category wise rule
        result = []
        for categ_id in category_list_ids:
            waqt_id = False
            rule_ids = col_by_category.get(categ_id)
            if categ_id.code == 'DED':
                waqt_id = self.env['hr.salary.rule'].search([('code', '=', 'waqf')])
                if waqt_id:
                    rule_ids = rule_ids | waqt_id
            if not rule_ids:
                continue
            result.append({categ_id: rule_ids.sorted(lambda l: l.sequence)})
        return result

    def action_go_back(self):
        action = self.env.ref('eq_batch_payslip_report.action_wizard_batch_payslip_report').read()[0]
        action['res_id'] = self.id
        self.write({'state': 'choose'})
        return action


class eq_batch_payslip_report_report_batch_payslip_template(models.AbstractModel):
    _name = 'report.eq_batch_payslip_report.report_batch_payslip_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name('eq_batch_payslip_report.report_batch_payslip_template')
        wizard_id = self.env['wizard.batch.payslip.report'].browse(data.get('id'))
        batch_id = wizard_id.batch_id
        get_header = wizard_id.get_header(batch_id)
        get_rule_list = []
        for header_dict in get_header:
            for rule_ids in header_dict.values():
                for rule_id in rule_ids:
                    get_rule_list.append(rule_id)
        
        total_rule_sum_dict = {}
        for rule in get_rule_list:
            total_rule_sum_dict[rule] = 0.0

        for slip in batch_id.slip_ids:
            for rule in get_rule_list:
                line = slip.line_ids.filtered(
                    lambda l: l.salary_rule_id.code == rule.code
                )
                amount = line.total or 0.0
                total_rule_sum_dict[rule] += amount
        return {
            'doc_ids': self.ids,
            'doc_model': report,
            'docs': batch_id,
            'data': data,
            'batch_id': batch_id,
            '_get_header': get_header,
            '_get_rule_list': get_rule_list,
            'total_rule_sum_dict': total_rule_sum_dict,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
