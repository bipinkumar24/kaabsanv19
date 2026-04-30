# -*- coding: utf-8 -*-
from odoo import Command, api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # ── Single "Fleet / Asset" column using a Reference field ─────────────────
    # The user first picks the type (Fleet Vehicle OR Asset) then the record.
    # Stored in DB as e.g.  'fleet.vehicle,12'  or  'account.asset,7'
    linked_to = fields.Reference(
        selection=[
            ('fleet.vehicle',  'Fleet Vehicle'),
            ('account.asset',  'Asset'),
        ],
        string='Fleet / Asset',
        index=True,
        copy=True,
        help="Select the fleet vehicle OR the asset this item is being purchased for.",
    )

    # ── Hidden Many2one helpers – used only for grouping in purchase.report ───
    # These are kept in sync with `linked_to` via an onchange + write override.
    _fleet_vehicle_id = fields.Many2one(
        comodel_name='fleet.vehicle',
        string='Fleet Vehicle (internal)',
        store=True,
        index=True,
        copy=False,
    )
    _asset_id = fields.Many2one(
        comodel_name='account.asset',
        string='Asset (internal)',
        store=True,
        index=True,
        copy=False,
    )

    asset_tag = fields.Many2many(
        comodel_name='asset.tag',
        relation='purchase_order_line_asset_tag_rel',
        column1='order_line_id',
        column2='tag_id',
        string='Asset Tag',
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Keep helper fields in sync whenever linked_to changes
    # ─────────────────────────────────────────────────────────────────────────
    @api.onchange('linked_to')
    def _onchange_linked_to(self):
        self._sync_helpers()

    def _sync_helpers(self):
        for line in self:
            ref = line.linked_to
            if ref and ref._name == 'fleet.vehicle':
                line._fleet_vehicle_id = ref.id
                line._asset_id = False
            elif ref and ref._name == 'account.asset':
                line._asset_id = ref.id
                line._fleet_vehicle_id = False
                line.asset_tag = [Command.set(ref.asset_tag.ids)]
            else:
                line._fleet_vehicle_id = False
                line._asset_id = False

    def write(self, vals):
        res = super().write(vals)
        if 'linked_to' in vals:
            self._sync_helpers()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_helpers()
        return records

    # ── Carry the tag to vendor bill lines ────────────────────────────────────
    def _prepare_account_move_line(self, move=False):
        vals = super()._prepare_account_move_line(move)
        if self.linked_to:
            vals['linked_to'] = '%s,%s' % (self.linked_to._name, self.linked_to.id)
        return vals
