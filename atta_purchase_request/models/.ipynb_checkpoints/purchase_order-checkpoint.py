from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.request_line_id')
    def _compute_request_line(self):
        for rec in self:
            rec.request_line_ids = rec.order_line.mapped('request_line_id')
            rec.request_line_count = len(rec.request_line_ids)

    request_line_ids = fields.Many2many(
        comodel_name='purchase.request.line',
        string='Purchase Request Lines',
        compute='_compute_request_line',
        readonly=True,
    )
    request_line_count = fields.Integer(
        compute='_compute_request_line'
    )

    def _set_purchase_requests_to_final_state(self):
        requests = self.request_line_ids.mapped('request_id')
        done_requests = requests.filtered(lambda r: r.state == 'done')
        done_requests.write({
            'state': 'final',
        })

    def button_draft(self):
        res = super(PurchaseOrder, self).button_draft()
        self._set_purchase_requests_to_final_state()
        return res

    def button_unlock(self):
        res = super(PurchaseOrder, self).button_unlock()
        self._set_purchase_requests_to_final_state()
        return res

    def action_view_request_line(self):
        [action] = self.env.ref(
            'atta_purchase_request.purchase_request_line_action').read()
        action.update({
            'domain': [('id', 'in', self.request_line_ids.ids)],
        })
        return action


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    request_line_id = fields.Many2one(
        comodel_name='purchase.request.line',
        string='Request Line',
        readonly=True,
    )

