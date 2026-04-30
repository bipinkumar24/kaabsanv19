# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ModelAccessRights(models.Model):
    """This class is used to detect, which all options want to hide from the
    specified group and model"""
    _name = "access.right"
    _inherit = "mail.thread"
    _description = "Manage Modules Access Control"

    model_id = fields.Many2one("ir.model", ondelete="cascade", required=True,
                               help="select the model")
    groups_id = fields.Many2one("res.groups", required=True,
                                help="select the group")
    is_delete = fields.Boolean(string="Can not Delete", help="hide the delete option")
    is_export = fields.Boolean(string="Can not Export",
                               help="hide the 'Export All'"
                                    " option from list view")
    is_create_or_update = fields.Boolean(string="Can not Create/Update",
                                         help="hide the create option from list"
                                              " as well as form view")
    is_archive = fields.Boolean(string="Can not Archive/UnArchive",
                                help="hide the archive option")
    name = fields.Char(string="Order Reference", readonly=True,
                       default=lambda self: _("New"))

    @api.model
    def create(self, vals):
        """This function is used to create the sequence number for this model"""
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "access.right") or _("New")
        return super().create(vals)

    @api.model
    def get_user_view_access(self, model_name):
        """Return aggregated UI restrictions for the current user and model."""
        restrictions = {
            "is_delete": False,
            "is_export": False,
            "is_create_or_update": False,
            "is_archive": False,
        }
        if not model_name or self.env.is_admin():
            return restrictions

        access_rules = self.sudo().search([
            ("model_id.model", "=", model_name),
            ("groups_id", "in", self.env.user.groups_id.ids),
        ])
        for rule in access_rules:
            restrictions["is_delete"] = restrictions["is_delete"] or rule.is_delete
            restrictions["is_export"] = restrictions["is_export"] or rule.is_export
            restrictions["is_create_or_update"] = (
                restrictions["is_create_or_update"] or rule.is_create_or_update
            )
            restrictions["is_archive"] = restrictions["is_archive"] or rule.is_archive
        return restrictions
