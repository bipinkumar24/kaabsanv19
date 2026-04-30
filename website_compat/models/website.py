from odoo import models


class Website(models.Model):
    _inherit = 'website'

    def _control_third_party_trackers_in_html(self, html):
        # Stub for stale database views referencing this method from a removed module.
        # Returns HTML unchanged; the original method filtered third-party trackers.
        return html or ''
