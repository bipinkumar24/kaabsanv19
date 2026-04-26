from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Lead(models.Model):
    _inherit = 'crm.lead'

    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Individual'), ('company', 'Company')],
                                    compute='_compute_company_type', inverse='_write_company_type', default='person')
    is_company = fields.Boolean(string='Is a Company', default=False,
                                help="Check if the contact is a company, otherwise it is a person")
    commercial_reg = fields.Binary(string='Commercial Registration', attachment=False)
    business_license = fields.Binary(string='Business License', attachment=False)
    passport = fields.Binary(string='Passport', attachment=False)
    article_of_association = fields.Binary(string='Article of Association', attachment=False)
    mou = fields.Binary(string='MOU', attachment=False,)
    minutes = fields.Binary(string='Minutes', attachment=False,)
    resolution_latter = fields.Binary(string='Resolution Latter', attachment=False)
    pickup_location_id = fields.Many2one('reservation.location', string='Pickup Location')
    drop_location_id = fields.Many2one('reservation.location', string='Drop Location')
    p_name = fields.Char(string='Project Name')
    # site_1 = fields.Char('Site Location 1')
    # site_2 = fields.Char('Site Location 2')

    @api.model
    def create(self, vals):
        rec = super(Lead, self).create(vals)
        rec._check_required_approval_fields()
        rec.remark_ids = [(0, 0, {'name': "New Created",
                                           'user_id': self.env.user.id,
                                           'remark_datettime': fields.Datetime.now(),
                                           'remark_type': 'approve'
                                           })]
        return rec

    def write(self, vals):
        res = super(Lead, self).write(vals)
        self._check_required_approval_fields()
        return res

    def _check_required_approval_fields(self):
        for rec in self:
            missing_fields = rec.next_approval_id.fields_ids.filtered(lambda field: not rec[field.name])
            if missing_fields:
                required_fields = ", ".join(missing_fields.mapped('field_description'))
                raise ValidationError("Required Fields are %r" % required_fields)

    @api.depends('next_approval_id', 'next_approval_id.is_customer_doc_required')
    def _compute_is_customer_doc_required(self):
        for rec in self:
            rec.is_customer_doc_required = rec.next_approval_id.is_customer_doc_required

    def _write_company_type(self):
        for partner in self:
            partner.is_company = partner.company_type == 'company'

    @api.depends('next_approval_id', 'next_approval_id.approval_user_ids')
    def _compute_next_approval_user_id(self):
        for rec in self:
            rec.next_approval_user_ids = [(6, 0, rec.next_approval_id.approval_user_ids.ids)]

    @api.depends('next_approval_id', 'next_approval_user_ids')
    def _compute_is_button(self):
        for rec in self:
            rec.is_last_level = False
            if self.env.user.id in rec.next_approval_user_ids.ids:
                rec.is_button = True
            else:
                rec.is_button = False

            if not rec.next_approval_id or rec.next_approval_id.is_last_approval or rec.next_approval_id.is_reject:
                rec.is_button = False
            if rec.next_approval_id.is_last_approval:
                rec.is_last_level = True

    def _get_next_approval_id(self):
        rec = self.env['approval.level.crm'].search([('level', '=', 1)])
        return rec.id

    next_approval_id = fields.Many2one('approval.level.crm', string='Next Approval', tracking=True,
                                       default=_get_next_approval_id)
    next_approval_user_ids = fields.Many2many('res.users', string='Next Approval By',
                                              compute='_compute_next_approval_user_id', store=True)
    is_button = fields.Boolean('Is button', compute='_compute_is_button')
    is_last_level = fields.Boolean('Is button', compute='_compute_is_button')
    remark_ids = fields.One2many('remarks.approval.crm', 'lead_id', string='Remarks', tracking=True)
    is_customer_doc_required = fields.Boolean(string='Is Customer Doc Required',
                                              compute='_compute_is_customer_doc_required')

    def action_approve(self):
        view_id = self.env.ref('salam_crm.crm_remark_wizard_wizard_view').id
        return {'type': 'ir.actions.act_window',
                'name': _('Remarks'),
                'res_model': 'crm.remark.wizard',
                'target': 'new',
                'view_mode': 'form',
                'views': [[view_id, 'form']],
                }

    @api.depends('is_company')
    def _compute_company_type(self):
        for partner in self:
            partner.company_type = 'company' if partner.is_company else 'person'
