import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PartnerLedgerWizard(models.TransientModel):
    _name = 'partner.ledger.wizard'
    _description = 'Partner Ledger Report Wizard'

    date_from = fields.Date(string='Start Date', required=True, default=lambda self: fields.Date.context_today(self).replace(day=1))
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.context_today)
    partner_ids = fields.Many2many('res.partner', string='Partners', domain=[('parent_id', '=', False)])
    partner_category_ids = fields.Many2many('res.partner.category', string='Partner Tags')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    include_reconciled = fields.Boolean(string='Include Fully Reconciled Entries', default=True)
    only_with_movement = fields.Boolean(string='Only Partners With Movements', default=True)
    show_details = fields.Boolean(string='Show Invoice Details', default=False, 
        help="Show invoice line details and delivery address for sales and purchase transactions")
    journal_ids = fields.Many2many('account.journal', string='Journals', 
        help="Select specific journals to include in the report. Leave empty to include all journals.")
    user_id = fields.Many2one('res.users', string='Salesperson',
        help="Filter partners by their assigned salesperson")
    summary_by_salesperson = fields.Boolean(string='Summary by Salesperson', default=False,
        help="Show summary report grouped by salesperson instead of detailed partner ledger")
    balance_confirmation = fields.Boolean(string='Balance Confirmation Request', default=False,
        help="Include a balance confirmation request section in the report")
    
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from > record.date_to:
                raise ValidationError(_("Start date must be less than or equal to end date."))
    
    def action_print_pdf(self):
        """Generate PDF report"""
        # Get partners based on selection criteria
        partners = self._get_partners()
        
        # If specific partners are selected, use them regardless of whether they have movements
        if self.partner_ids:
            partners = self.partner_ids
        elif not partners:
            # If no partners found based on criteria, get all partners that have move lines
            partners = self._get_all_partners_with_moves()
            
            # If still no partners, just get the first few partners
            if not partners:
                partners = self.env['res.partner'].search([('customer_rank', '>', 0)], limit=5)
        
        _logger.info("Generating report for %s partners", len(partners))
        
        # Prepare report data
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'company_id': self.company_id.id,
            'include_reconciled': self.include_reconciled,
            'partner_ids': partners.ids,
            'report_name': 'Partner Ledger',
            'show_details': self.show_details,
            'journal_ids': self.journal_ids.ids if self.journal_ids else [],
            'user_id': self.user_id.id if self.user_id else False,
            'summary_by_salesperson': self.summary_by_salesperson,
            'balance_confirmation': self.balance_confirmation,
        }
        
        # Return the report action
        if self.summary_by_salesperson:
            return self.env.ref('an_partner_ledger_adv.action_report_partner_ledger_summary').report_action(self, data=data)
        else:
            # If only one partner, pass it as docids
            if len(partners) == 1:
                return self.env.ref('an_partner_ledger_adv.action_report_partner_ledger').report_action(partners[0], data=data)
            else:
                return self.env.ref('an_partner_ledger_adv.action_report_partner_ledger').report_action(self, data=data)
    
    def _get_all_partners_with_moves(self):
        """Get all partners that have move lines regardless of date range"""
        move_line_domain = [
            ('company_id', '=', self.company_id.id),
            ('partner_id', '!=', False),
            ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable']),
            ('move_id.state', '=', 'posted'),
        ]
        
        # Add journal filter if specified
        if self.journal_ids:
            move_line_domain.append(('journal_id', 'in', self.journal_ids.ids))
            
        partner_ids = self.env['account.move.line'].search(move_line_domain).mapped('partner_id').ids
        partners = self.env['res.partner'].browse(partner_ids)
        
        # Apply salesperson filter if specified
        if self.user_id:
            partners = partners.filtered(lambda p: p.user_id.id == self.user_id.id)
            
        return partners
    
    def _get_partners(self):
        """Get partners based on selection criteria"""
        domain = []
        
        # Add company filter if multi-company is enabled
        if self.env.user.has_group('base.group_multi_company'):
            domain.append(('company_id', 'in', [self.company_id.id, False]))
        
        # Filter by selected partners if any
        if self.partner_ids:
            domain.append(('id', 'in', self.partner_ids.ids))
            # If specific partners are selected, don't filter by movements
            partners = self.env['res.partner'].search(domain)
            _logger.info("Found %s specifically selected partners", len(partners))
            return partners
        
        # Filter by partner categories if any
        if self.partner_category_ids:
            domain.append(('category_id', 'in', self.partner_category_ids.ids))
            
        # Filter by salesperson if specified
        if self.user_id:
            domain.append(('user_id', '=', self.user_id.id))
        
        # Only include partners with accounting entries
        if self.only_with_movement:
            # Get partners with move lines in the date range
            move_line_domain = [
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to),
                ('company_id', '=', self.company_id.id),
                ('partner_id', '!=', False),
                ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable']),
                ('move_id.state', '=', 'posted'),
            ]
            
            # Add journal filter if specified
            if self.journal_ids:
                move_line_domain.append(('journal_id', 'in', self.journal_ids.ids))
            
            if not self.include_reconciled:
                move_line_domain.append(('full_reconcile_id', '=', False))
                
            partner_ids = self.env['account.move.line'].search(move_line_domain).mapped('partner_id').ids
            if partner_ids:
                domain.append(('id', 'in', partner_ids))
            else:
                _logger.warning("No partners found with move lines in the selected date range")
                return self.env['res.partner']
        
        partners = self.env['res.partner'].search(domain)
        _logger.info("Found %s partners matching the criteria: %s", len(partners), domain)
        return partners
