from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection([
        ('initial', 'Draft'),
        ('procurement', 'Waiting for Procurement Manager'),
        ('general', 'Waiting for General Manager'),
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='initial', tracking=True)

    tag_name = fields.Char('Tags', compute='_compute_tag_name', store=True)
    request_uid = fields.Many2one(
        comodel_name='res.users',
        string='Requester',
        readonly=True,
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department',
        readonly=True,
    )

    @api.depends('partner_id')
    def _compute_tag_name(self):
        for rec in self:
            rec.tag_name = " ".join(rec.partner_id.category_id.mapped('name'))

    def action_submit(self):
        self.state = 'procurement'
    def action_procurement(self):
        self.state = 'general'
    def action_general(self):
        self.state = 'draft'

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

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for rec in self:
            rec.picking_ids.write({'request_uid': rec.request_uid.id , 'department_id': rec.department_id.id})
        return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    request_line_id = fields.Many2one(
        comodel_name='purchase.request.line',
        string='Request Line',
        readonly=True,
    )
