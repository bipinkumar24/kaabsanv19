from collections import defaultdict
from datetime import date
import calendar

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class BudgetComparisonWizard(models.TransientModel):
    _name = 'budget.comparison.wizard'
    _description = 'Budget Comparison Wizard'


    year_from = fields.Selection(
        [(str(y), str(y)) for y in range(2000, 2100)],
        string="From Year",
        required=True
    )
    year_to = fields.Selection(
        [(str(y), str(y)) for y in range(2000, 2100)],
        string="To Year",
        required=True
    )
    quarter_from = fields.Selection([
        ('q1', 'Q1 (Jan-Mar)'),
        ('q2', 'Q2 (Apr-Jun)'),
        ('q3', 'Q3 (Jul-Sep)'),
        ('q4', 'Q4 (Oct-Dec)')
    ], string="Quarter")

    half_year_from = fields.Selection([
        ('h1', 'H1 (Jan-Jun)'),
        ('h2', 'H2 (Jul-Dec)')
    ], string="Half Year")
    quarter_to = fields.Selection([
        ('q1', 'Q1 (Jan-Mar)'),
        ('q2', 'Q2 (Apr-Jun)'),
        ('q3', 'Q3 (Jul-Sep)'),
        ('q4', 'Q4 (Oct-Dec)')
    ], string="Quarter")

    half_year_to = fields.Selection([
        ('h1', 'H1 (Jan-Jun)'),
        ('h2', 'H2 (Jul-Dec)')
    ], string="Half Year")

    from_start_date = fields.Date("From Start Date", compute='_compute_dates', store=True)
    from_end_date = fields.Date("From End Date", compute='_compute_dates', store=True)
    to_start_date = fields.Date("To Start Date", compute='_compute_dates', store=True)
    to_end_date = fields.Date("To End Date", compute='_compute_dates', store=True)

    def get_selection_label(self, field_name, value):
        field = self._fields.get(field_name)
        if field and hasattr(field, 'selection'):
            selection_dict = dict(field.selection)
            return selection_dict.get(value)
        return ''
    

    @api.depends('year_from', 'year_to', 'quarter_from', 'quarter_to', 'half_year_from', 'half_year_to')
    def _compute_dates(self):
        for wizard in self:
            if wizard.year_from:
                y = int(wizard.year_from)
                wizard.from_start_date = date(y, 1, 1)
                wizard.from_end_date = date(y, 12, 31)
            if wizard.year_to:
                y = int(wizard.year_to)

                if not wizard.year_from:
                    raise ValidationError('Please select From Year')

                if wizard.year_to <= wizard.year_from:
                    raise ValidationError("Please select correct year")

                wizard.to_start_date = date(y, 1, 1)
                wizard.to_end_date = date(y, 12, 31)

            if wizard.quarter_from and wizard.year_from:
                y = int(wizard.year_from)
                q_dates = {
                    'q1': (1, 3),
                    'q2': (4, 6),
                    'q3': (7, 9),
                    'q4': (10, 12),
                }
                start_m, end_m = q_dates[wizard.quarter_from]
                last_day = calendar.monthrange(y, end_m)[1]
                wizard.from_start_date = date(y, start_m, 1)
                wizard.from_end_date = date(y, end_m, last_day)

            if wizard.half_year_from and wizard.year_from:
                y = int(wizard.year_from)
                h_dates = {
                    'h1': (1, 6),
                    'h2': (7, 12),
                }
                start_m, end_m = h_dates[wizard.half_year_from]
                last_day = calendar.monthrange(y, end_m)[1]
                wizard.from_start_date = date(y, start_m, 1)
                wizard.from_end_date = date(y, end_m, last_day)

            if wizard.quarter_to and wizard.year_to:
                y = int(wizard.year_to)
                q_dates = {
                    'q1': (1, 3),
                    'q2': (4, 6),
                    'q3': (7, 9),
                    'q4': (10, 12),
                }
                start_m, end_m = q_dates[wizard.quarter_to]
                last_day = calendar.monthrange(y, end_m)[1]
                wizard.to_start_date = date(y, start_m, 1)
                wizard.to_end_date = date(y, end_m, last_day)

            if wizard.half_year_to and wizard.year_to:
                y = int(wizard.year_to)
                h_dates = {
                    'h1': (1, 6),
                    'h2': (7, 12),
                }
                start_m, end_m = h_dates[wizard.half_year_to]
                last_day = calendar.monthrange(y, end_m)[1]
                wizard.to_start_date = date(y, start_m, 1)
                wizard.to_end_date = date(y, end_m, last_day)


    def _get_budget_domain(self, start_date, end_date):
        return [
            ('state', '=', 'confirmed'),
            ('date_from', '<=', start_date),
            ('date_to', '>=', end_date),
        ]

    def _line_key(self, line):
        return line.account_id.id or line.auto_account_id.id or line.id

    def _line_category(self, line):
        return line.account_id.display_name or line.auto_account_id.display_name or line.name or _('Undefined')

    def _aggregate_budget_lines(self, budgets):
        summary = defaultdict(lambda: {
            'category': '',
            'planned': 0.0,
            'actual': 0.0,
        })
        for budget in budgets:
            for line in budget.budget_line_ids:
                key = self._line_key(line)
                summary[key]['category'] = self._line_category(line)
                summary[key]['planned'] += line.budget_amount or 0.0
                summary[key]['actual'] += line.achieved_amount or 0.0
        return summary

    def get_report_data(self):
        self.ensure_one()

        if not self.from_start_date or not self.from_end_date or not self.to_start_date or not self.to_end_date:
            raise ValidationError(_("Please select valid date ranges."))

        budgets_from = self.env['budget.analytic'].search(self._get_budget_domain(self.from_start_date, self.from_end_date))
        budgets_to = self.env['budget.analytic'].search(self._get_budget_domain(self.to_start_date, self.to_end_date))

        from_budget_map = self._aggregate_budget_lines(budgets_from)
        to_budget_map = self._aggregate_budget_lines(budgets_to)

        all_keys = sorted(set(from_budget_map) | set(to_budget_map), key=lambda key: (
            to_budget_map.get(key, from_budget_map.get(key, {})).get('category', '')
        ))
        report_lines = []

        for key in all_keys:
            previous_values = from_budget_map.get(key, {})
            current_values = to_budget_map.get(key, {})
            actual_prev = previous_values.get('actual', 0.0)
            planned = current_values.get('planned', 0.0)
            actual_current = current_values.get('actual', 0.0)
            variance_value = actual_current - planned
            variance_percent = (variance_value / planned * 100) if planned else 0.0
            yoy_change = ((actual_current - actual_prev) / actual_prev * 100) if actual_prev else 0.0

            report_lines.append({
                'category': current_values.get('category') or previous_values.get('category') or '',
                'actual_previous': round(actual_prev, 2),
                'planned': round(planned, 2),
                'actual_current': round(actual_current, 2),
                'variance_value': round(variance_value, 2),
                'variance_percent': round(variance_percent, 2),
                'yoy_change': round(yoy_change, 2),
            })

        return {
            'report_lines': report_lines,
            'year_from': self.year_from,
            'year_to': self.year_to,
            'half_year_from': self.get_selection_label('half_year_from', self.half_year_from),
            'quarter_from': self.get_selection_label('quarter_from', self.quarter_from),
            'half_year_to': self.get_selection_label('half_year_to', self.half_year_to),
            'quarter_to': self.get_selection_label('quarter_to', self.quarter_to),
            'from_start_date': str(self.from_start_date),
            'from_end_date': str(self.from_end_date),
            'to_start_date': str(self.to_start_date),
            'to_end_date': str(self.to_end_date),
        }
        

    def action_generate_report(self):
        datas = self.get_report_data()
        return self.env.ref('budget_comparison.action_budget_comparison_wizard_report').report_action(self, data=datas)
