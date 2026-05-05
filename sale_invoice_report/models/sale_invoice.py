from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    project_details = fields.Char(string="Project Details")

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.project_details:
            invoice_vals.update({
                'project_details': self.project_details
            })
        return invoice_vals


class AccountMove(models.Model):
    _inherit = "account.move"

    project_details = fields.Char(string="Project Details")
