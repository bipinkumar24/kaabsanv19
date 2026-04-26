from odoo import models, fields, api
import re

class HrEmployee(models.Model):
    _inherit = 'hr.employee'


    old_number = fields.Char(string="Old Number")

    def _create_work_contact(self):
        """Create linked partner for employee if not exists"""
        if not self.work_contact_id:
            partner = self.env['res.partner'].create({
                'name': f"{self.identification_id or ''}  {self.name}",
            })
            self.work_contact_id = partner.id
            self.old_number = self.identification_id

    @api.model_create_multi
    def create(self, vals_list):
        employees = super().create(vals_list)
        # Create partner automatically after employee creation
        employees._create_work_contact()
        return employees

    def action_update_partner_name(self):
        """Server Action: Update partner name with employee unique number"""
        for emp in self:
            if emp.work_contact_id and emp.identification_id:
                partner_name = emp.work_contact_id.name.strip()
                current_id = emp.identification_id.strip()
                old_id = emp.old_number.strip() if emp.old_number else ""

                # Case 1: Same as old_number → skip update
                if old_id and current_id == old_id:
                    continue

                new_name = partner_name

                # Case 2: Replace old_number if exists in name
                if old_id:
                    pattern = rf"^{re.escape(old_id)}\s*"
                    new_name = re.sub(pattern, "", partner_name).strip()

                # Case 3: Prepend the new identification_id
                new_name = f"{current_id} {new_name}".strip()

                # Update only if changed
                if emp.work_contact_id.name != new_name:
                    emp.work_contact_id.name = new_name
                    emp.old_number = current_id  # Store the latest number
