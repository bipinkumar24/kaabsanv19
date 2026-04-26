from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_round


class CarReservation(models.Model):
    _inherit = "car.reservation"

    lead_id = fields.Many2one('crm.lead', string='Car Leads')
    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True)

    # pickup_location_id = fields.Many2one('reservation.location', string='Pickup Location')
    # drop_location = fields.Many2one('reservation.location', string='Drop Location')

    @api.onchange('lead_id')
    def onchange_lead_id(self):
        for rec in self:
            rec.partner_id = rec.lead_id.partner_id
            # Odoo 19 migration: these are custom crm.lead fields and may not exist in every database.
            # Old direct assignments kept for migration reference:
            # rec.pickup_location_id = rec.lead_id.pickup_location_id
            # rec.drop_location_id = rec.lead_id.drop_location_id
            if not rec.lead_id:
                rec.pickup_location_id = False
                rec.drop_location_id = False
                continue
            if rec.lead_id and 'pickup_location_id' in rec.lead_id._fields:
                rec.pickup_location_id = rec.lead_id.pickup_location_id
            if rec.lead_id and 'drop_location_id' in rec.lead_id._fields:
                rec.drop_location_id = rec.lead_id.drop_location_id

    # @api.onchange('lead_id')
    # def onchange_lead_id(self):
    #     for rec in self:
    #         rec.site_1 = rec.lead_id.site_1
    #
    # @api.onchange('lead_id')
    # def onchange_lead_id(self):
    #     for rec in self:
    #         rec.site_2 = rec.lead_id.site_2
