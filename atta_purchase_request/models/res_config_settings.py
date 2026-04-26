from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    has_pr_4th_approve = fields.Boolean(
        string='4th Approval Management?',
    )
    pr_4th_approve_amount = fields.Monetary(
        string='Minimum Amount',
        currency_field='company_currency_id',
        default=0,
    )
    is_required_vendor_in_pr = fields.Boolean(
        string='Required Preferred Vendor in PR?',
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param(
            'atta_purchase_request.has_pr_4th_approve',
            self.has_pr_4th_approve
        )
        self.env['ir.config_parameter'].set_param(
            'atta_purchase_request.pr_4th_approve_amount',
            self.pr_4th_approve_amount or 0
        )
        self.env['ir.config_parameter'].set_param(
            'atta_purchase_request.is_required_vendor_in_pr',
            self.is_required_vendor_in_pr
        )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            has_pr_4th_approve=params.get_param(
                'atta_purchase_request.has_pr_4th_approve',
                default=False
            ),
            pr_4th_approve_amount=float(params.get_param(
                'atta_purchase_request.pr_4th_approve_amount',
                default=0
            )),
            is_required_vendor_in_pr=params.get_param(
                'atta_purchase_request.is_required_vendor_in_pr',
                default=False
            ),
        )
        return res
