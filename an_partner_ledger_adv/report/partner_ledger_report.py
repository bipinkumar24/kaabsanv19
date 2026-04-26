import logging

import num2words
from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PartnerLedgerReport(models.AbstractModel):
    _name = 'report.an_partner_ledger_adv.report_partner_ledger'
    _description = 'Partner Ledger Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            raise UserError(_('No data provided for the report.'))
        
        # Extract parameters from data
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        company_id = data.get('company_id')
        include_reconciled = data.get('include_reconciled', True)
        show_details = data.get('show_details', False)
        journal_ids = data.get('journal_ids', [])
        balance_confirmation = data.get('balance_confirmation', False)
        
        # Get the company record
        company = self.env['res.company'].browse(company_id)
        
        # Get partners - if docids is provided, use those specific partners
        if docids:
            partner_ids = [docids] if isinstance(docids, int) else docids
        else:
            partner_ids = data.get('partner_ids', [])
        
        partners = self.env['res.partner'].browse(partner_ids)
        
        # Prepare report data
        docs = []
        for partner in partners:
            partner_data = self._get_partner_ledger_data(
                partner, date_from, date_to, company, include_reconciled, show_details, journal_ids)
            # Add data regardless of whether there are lines or initial balance
            docs.append(partner_data)
        
        # If no partners found, add a dummy entry
        if not docs:
            dummy_partner = self.env['res.partner'].search([], limit=1)
            if dummy_partner:
                docs.append({
                    'partner': dummy_partner,
                    'initial_balance': 0.0,
                    'move_lines': [],
                    'ending_balance': 0.0,
                })
        
        _logger.info("Report data: %s partners, date range: %s to %s", len(docs), date_from, date_to)
        
        # Get amount in words for each partner's balance
        for doc in docs:
            amount = abs(doc['ending_balance'])
            currency = company.currency_id
            lang = self.env.user.lang or 'en_US'
            
            try:
                amount_in_words = num2words.num2words(amount, lang=lang.split('_')[0])
                if lang.startswith('ar'):
                    # For Arabic, we might need specific implementation
                    # This is a simplified version
                    doc['amount_in_words'] = f"{amount_in_words} {currency.name}"
                else:
                    # For other languages
                    doc['amount_in_words'] = f"{amount_in_words} {currency.name}"
            except NotImplementedError:
                # Fallback for languages not supported by num2words
                doc['amount_in_words'] = f"{amount} {currency.name}"
        
        return {
            'doc_ids': partner_ids,
            'doc_model': 'res.partner',
            'docs': docs,
            'date_from': fields.Date.to_date(date_from) if isinstance(date_from, str) else date_from,
            'date_to': fields.Date.to_date(date_to) if isinstance(date_to, str) else date_to,
            'company': company,
            'show_details': show_details,
            'balance_confirmation': balance_confirmation,
            'journals': self.env['account.journal'].browse(journal_ids) if journal_ids else self.env['account.journal'].search([]),
            'current_date_time': fields.Datetime.now()
        }
    
    def _get_partner_ledger_data(self, partner, date_from, date_to, company, include_reconciled, show_details, journal_ids):
        # Get initial balance
        initial_balance = self._get_initial_balance(partner, date_from, company, include_reconciled, journal_ids)
        
        # Get move lines for the period
        move_lines = self._get_move_lines(partner, date_from, date_to, company, include_reconciled, show_details, journal_ids)
        
        # Calculate ending balance
        ending_balance = initial_balance
        for line in move_lines:
            ending_balance += line['debit'] - line['credit']
        
        _logger.info(
            "Partner %s: found %s move lines, initial balance: %s",
            partner.name,
            len(move_lines),
            initial_balance,
        )
        
        return {
            'partner': partner,
            'initial_balance': initial_balance,
            'move_lines': move_lines,
            'ending_balance': ending_balance,
            'total_debit': sum(line['debit'] for line in move_lines),
            'total_credit': sum(line['credit'] for line in move_lines),
        }
    
    def _get_initial_balance(self, partner, date_from, company, include_reconciled, journal_ids):
        domain = [
            ('partner_id', '=', partner.id),
            ('date', '<', date_from),
            ('company_id', '=', company.id),
            ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable']),
            ('move_id.state', '=', 'posted'),
        ]
        
        # Add journal filter if specified
        if journal_ids:
            domain.append(('journal_id', 'in', journal_ids))
        
        if not include_reconciled:
            domain.append(('full_reconcile_id', '=', False))
        
        _logger.info("Initial balance domain: %s", domain)
        move_lines = self.env['account.move.line'].search(domain)
        
        initial_balance = 0.0
        for line in move_lines:
            initial_balance += line.debit - line.credit
        
        return initial_balance
    
    def _get_move_lines(self, partner, date_from, date_to, company, include_reconciled, show_details, journal_ids):
        domain = [
            ('partner_id', '=', partner.id),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id', '=', company.id),
            ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable']),
            ('move_id.state', '=', 'posted'),
        ]
        
        # Add journal filter if specified
        if journal_ids:
            domain.append(('journal_id', 'in', journal_ids))
        
        if not include_reconciled:
            domain.append(('full_reconcile_id', '=', False))
        
        _logger.info("Move lines domain: %s", domain)
        move_lines = self.env['account.move.line'].search(
            domain, order='date, move_id, id')
        
        result = []
        running_balance = self._get_initial_balance(partner, date_from, company, include_reconciled, journal_ids)
        
        for line in move_lines:
            # Update running balance
            running_balance += line.debit - line.credit
            
            # Get a more descriptive type name based on journal type
            type_name = self._get_journal_type_display(line.journal_id)
            
            line_data = {
                'date': line.date,
                'move_name': line.move_id.name,
                'type': type_name,  # Display type instead of journal name
                'journal_type': line.journal_id.type,
                'account': line.account_id.code + ' ' + line.account_id.name,
                'ref': line.ref or '',
                'name': line.name or '',
                'debit': line.debit,
                'credit': line.credit,
                'balance': running_balance,
                'currency': line.currency_id,
                'amount_currency': line.amount_currency,
                'move_id': line.move_id.id,
                'invoice_lines': [],
                'is_invoice': False,
                'delivery_address': None
            }
            
            # If show_details is enabled and the journal is sale or purchase, get the invoice lines
            if show_details and line.journal_id.type in ['sale', 'purchase'] and line.move_id:
                # Try to get invoice lines from the move
                invoice = line.move_id
                
                # Add delivery address if available
                if hasattr(invoice, 'partner_shipping_id') and invoice.partner_shipping_id:
                    shipping_partner = invoice.partner_shipping_id
                    address_parts = []
                    if shipping_partner.street:
                        address_parts.append(shipping_partner.street)
                    if shipping_partner.street2:
                        address_parts.append(shipping_partner.street2)
                    if shipping_partner.city:
                        address_parts.append(shipping_partner.city)
                    if shipping_partner.state_id:
                        address_parts.append(shipping_partner.state_id.name)
                    if shipping_partner.zip:
                        address_parts.append(shipping_partner.zip)
                    if shipping_partner.country_id:
                        address_parts.append(shipping_partner.country_id.name)
                    
                    line_data['delivery_address'] = {
                        'name': shipping_partner.name,
                        'address': ', '.join(address_parts)
                    }
                
                if invoice and invoice.invoice_line_ids:
                    line_data['is_invoice'] = True
                    for inv_line in invoice.invoice_line_ids:
                        line_data['invoice_lines'].append({
                            'product_name': inv_line.product_id.name if inv_line.product_id else inv_line.name,
                            'quantity': inv_line.quantity,
                            'uom': inv_line.product_uom_id.name if inv_line.product_uom_id else '',
                            'price_unit': inv_line.price_unit,
                            'price_subtotal': inv_line.price_subtotal,
                            'price_total': inv_line.price_total,  # Added price_total which includes taxes
                        })
            
            result.append(line_data)
        
        return result
    
    def _get_journal_type_display(self, journal):
        """Get a user-friendly display name for journal type"""
        # Map the 5 journal types according to the screenshot and requirements
        journal_type_names = {
            'sale': 'Sales',
            'purchase': 'Purchase',
            'cash': 'Payment',    # Combine cash and bank as Payment
            'bank': 'Payment',    # Combine cash and bank as Payment
            'general': 'General'  # Correctly map general to General
        }
        
        # Return the friendly name for the journal type, or the journal name if type not in mapping
        return journal_type_names.get(journal.type, journal.name)


class PartnerLedgerSummaryReport(models.AbstractModel):
    _name = 'report.an_partner_ledger_adv.report_partner_ledger_summary'
    _description = 'Partner Ledger Summary Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            raise UserError(_('No data provided for the report.'))
        
        # Extract parameters from data
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        company_id = data.get('company_id')
        include_reconciled = data.get('include_reconciled', True)
        partner_ids = data.get('partner_ids', [])
        journal_ids = data.get('journal_ids', [])
        user_id = data.get('user_id')
        
        # Get the company record
        company = self.env['res.company'].browse(company_id)
        
        # Get the partners
        partners = self.env['res.partner'].browse(partner_ids)
        
        # Get the salesperson
        salesperson = self.env['res.users'].browse(user_id) if user_id else False
        
        # Prepare report data
        partner_ledger = self.env['report.an_partner_ledger_adv.report_partner_ledger']
        partners_data = []
        total_initial = 0
        total_debit = 0
        total_credit = 0
        total_balance = 0
        
        for partner in partners:
            partner_data = partner_ledger._get_partner_ledger_data(
                partner, date_from, date_to, company, include_reconciled, False, journal_ids)
            
            # Only include partners with activity or balance
            if partner_data['move_lines'] or partner_data['initial_balance'] != 0:
                partners_data.append(partner_data)
                total_initial += partner_data['initial_balance']
                total_debit += partner_data['total_debit']
                total_credit += partner_data['total_credit']
                total_balance += partner_data['ending_balance']
        
        return {
            'date_from': fields.Date.to_date(date_from) if isinstance(date_from, str) else date_from,
            'date_to': fields.Date.to_date(date_to) if isinstance(date_to, str) else date_to,
            'company': company,
            'partners_data': partners_data,
            'salesperson': salesperson,
            'journals': self.env['account.journal'].browse(journal_ids) if journal_ids else self.env['account.journal'].search([]),
            'total_initial': total_initial,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'total_balance': total_balance,
        }
