# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.tools import SQL


class PurchaseReport(models.Model):
    """
    Extend Purchase Analysis to allow grouping and filtering by Fleet Vehicle
    or Asset. We read from the hidden helper Many2one columns (_fleet_vehicle_id
    and _asset_id) that are kept in sync with the Reference field on the line.
    """
    _inherit = 'purchase.report'

    fleet_vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Fleet Vehicle',
        readonly=True,
    )
    asset_id = fields.Many2one(
        'account.asset',
        string='Asset',
        readonly=True,
    )

    def _select(self) -> SQL:
        return SQL(
            "%s, l.\"_fleet_vehicle_id\" AS fleet_vehicle_id, l.\"_asset_id\" AS asset_id",
            super()._select(),
        )

    def _group_by(self) -> SQL:
        return SQL(
            '%s, l."_fleet_vehicle_id", l."_asset_id"',
            super()._group_by(),
        )
