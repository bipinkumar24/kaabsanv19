# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import datetime
import calendar
from dateutil.relativedelta import *
from odoo.exceptions import UserError, ValidationError

class reject_request(models.TransientModel):
	_name = "reject.request"
	_description = "Reject request message wizard"



	message = fields.Char("Message")


	def update_employee_to_reject_request(self):
		loan_id = False
		if 'loan_id' in self.env.context:
			loan_id = self.env['loan.request'].browse(self.env.context.get('loan_id'))
			loan_id.update({
				'cancel_loan_employee_id' : self.env.user.id
				})
			template = self.env.ref('bi_hr_employee_loan.email_template_cancel_loan_request', raise_if_not_found=False)
			if template:
				template.send_mail(loan_id.id, force_send=True)
			loan_id.update({
				'stage' : 'cancel'
				})