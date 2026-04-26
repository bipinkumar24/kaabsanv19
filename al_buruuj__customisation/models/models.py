from odoo import _, api, fields, models
from odoo.exceptions import UserError


class bur_purchase_order(models.Model):
    _inherit = "purchase.order"
    _description = 'purchase.order Inherited'

    picking_type_idd = fields.Many2many(
        'stock.picking.type',
        domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]",
        help="This will determine operation type of incoming shipment")


class bur_stock_picking(models.Model):
    _inherit = "stock.picking"
    _description = 'stock_picking Inherited'

    vehicle_reg_number = fields.Char('Car Plate Number')
    vehicle_driver = fields.Char('Delivery Driver')


class bur_res_partner(models.Model):
    _inherit = "res.partner"
    _description = 'res.partner Inherited'

    @api.depends('total_due')
    def _compute_total_due(self):
        for rec in self:
            rec.total_due_OC = rec.total_due / 177.75

    total_due_OC = fields.Monetary('Total Due USD', compute=_compute_total_due)
    MRB_Customer = fields.Boolean('Murabaha Customer')
    MRB_Bank = fields.Char('Murabaha Bank')


class bur_account_payment(models.Model):
    _inherit = "account.payment"
    _description = 'account.payment Inherited'

    Vocher_number = fields.Char('Voucher Number')
    payment_Method = fields.Selection([('cs', 'Cash'), ('ck', 'Check')], default='cs')
    Check_number = fields.Char('Check Number')


class Users(models.Model):
    _inherit = "res.users"

    sale_order_can_approve = fields.Selection([('yes', 'Yes'), ('no', 'No')], 'Can Approve Sale?', default='no')
    sale_order_amount_limit = fields.Float("(SO) Amount Limit", digits=(16, 0))
    sale_order_discount_limit = fields.Float("(SO) Discount Limit", digits=(16, 0))


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    minimum_amount = fields.Float('Minimum Amount')
    maximum_amount = fields.Float('Maximum Amount')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        config_parameter = self.env['ir.config_parameter'].sudo()
        minimum_amount = config_parameter.get_param('sale_approval.minimum_amount', default=0)
        maximum_amount = config_parameter.get_param('sale_approval.maximum_amount', default=0)
        res.update(minimum_amount=float(minimum_amount or 0))
        res.update(maximum_amount=float(maximum_amount or 0))
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        config_parameter = self.env['ir.config_parameter'].sudo()
        config_parameter.set_param("sale_approval.minimum_amount", self.minimum_amount)
        config_parameter.set_param("sale_approval.maximum_amount", self.maximum_amount)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection(
        selection_add=[('waiting_for_approval', 'Waiting For Approval')],
        ondelete={'waiting_for_approval': 'set default'},
    )
    approver_id = fields.Many2one('res.users', 'Sale Order Approver', readonly=True, copy=False, tracking=True, default=lambda self: self.env.user)
    discount_notes = fields.Float('Discount Note')
    next_discount_amount = fields.Float('Next Discount Amount')

    def action_confirm(self):
        for sale_order in self:
            minimum_amount = 0.00
            maximum_amount = 0.00
            if self.env['ir.config_parameter'].sudo().get_param('sale_approval.minimum_amount'):
                minimum_amount = float(self.env['ir.config_parameter'].sudo().get_param('sale_approval.minimum_amount'))
            if self.env['ir.config_parameter'].sudo().get_param('sale_approval.maximum_amount'):
                maximum_amount = float(self.env['ir.config_parameter'].sudo().get_param('sale_approval.maximum_amount'))
            if sale_order.amount_total >= minimum_amount and sale_order.amount_total <= maximum_amount:
                if not self.env.user.sale_order_can_approve == 'yes':
                    raise UserError(_('You are not an Approver. Please click on "Ask for Approval".'))
                if not sale_order.amount_total <= self.env.user.sale_order_amount_limit:
                    raise UserError(_('Your approval limit is lesser then sale order total amount. Please click on "Ask for Approval".'))
        return super(SaleOrder, self).action_confirm()

    def get_discount(self):
        return self.env.context.get('discount_percentage', 0)

    def get_reason_notes(self):
        return self.env.context.get('discount_notes', '')

    def get_reason_note(self):
        return self.env.context.get('discount_notes', '')

    def escalate_order(self):
        self.ensure_one()
        template = self.env.ref('al_buruuj__customisation.email_template_sale_approval_mail')
        self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
        return True


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('discount')
    def onchang_discount_validate(self):
        if self.discount:
            approver_id = self.order_id.approver_id
            if not self.discount <= approver_id.sale_order_discount_limit:
                value = {
                    'discount': 00.0
                }
                warning = {
                    'title': _('Warning!'),
                    'message': _('Your discount limit is lesser than given discount.!')
                }
                return {'warning': warning, 'value': value}
