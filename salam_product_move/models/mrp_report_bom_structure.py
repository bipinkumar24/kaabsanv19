# -*- coding: utf-8 -*-

import json

from odoo import api, models, _
from odoo.tools import float_round

class ReportBomStructure(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'
    _description = 'BOM Structure Report'

    @api.model
    def _get_pdf_line(self, bom_id, product_id=False, qty=1, unfolded_ids=None, unfolded=False):
        data = super()._get_pdf_line(
            bom_id,
            product_id=product_id,
            qty=qty,
            unfolded_ids=unfolded_ids,
            unfolded=unfolded,
        )
        bom = self.env['mrp.bom'].browse(bom_id)
        materials = self._get_material_line(bom)
        labours = self._get_direct_labour_line(bom)
        overheads = self._get_direct_oh_line(bom)
        data.update({
            'total_materials': sum(m['duration_expected'] for m in materials),
            'cost_materials': sum(m['total'] for m in materials),
            'total_labours': sum(l['duration_expected'] for l in labours),
            'cost_labours': sum(l['total'] for l in labours),
            'total_ohs': sum(o['duration_expected'] for o in overheads),
            'cost_ohs': sum(o['total'] for o in overheads),
        })
        return data

    @api.model
    def get_materials(self, product_id=False, bom_id=False, qty=0, level=0):
        bom = self.env['mrp.bom'].browse(bom_id)
        product = self.env['product.product'].browse(product_id)
        lines = self._get_material_line(bom)
        values = {
            'bom_id': bom_id,
            'currency': self.env.company.currency_id,
            'operations': lines,
            'extra_column_count': self._get_extra_column_count()
        }
        return self.env.ref('salam_product_move.report_mrp_materials_line')._render({'data': values})

    def _get_material_line(self, bom):
        materials = []
        for material in bom.bom_material_cost_ids:
            duration_expected = material.planned_qty
            total = material.total_cost
            materials.append({
                'level': 0,
                'operation': material,
                'name': material.product_id.name,
                'duration_expected': duration_expected,
                'total': self.env.company.currency_id.round(total),
            })
        return materials

    def _get_direct_labour_line(self, bom):
        labours = []
        for labour in bom.bom_labour_cost_ids:
            duration_expected = labour.planned_qty
            total = labour.total_cost
            labours.append({
                'level': 0,
                'operation': labour,
                'name': labour.product_id.name,
                'duration_expected': duration_expected,
                'total': self.env.company.currency_id.round(total),
            })
        return labours

    def _get_direct_oh_line(self, bom):
        labours = []
        for labour in bom.bom_overhead_cost_ids:
            duration_expected = labour.planned_qty
            total = labour.total_cost
            labours.append({
                'level': 0,
                'operation': labour,
                'name': labour.product_id.name,
                'duration_expected': duration_expected,
                'total': self.env.company.currency_id.round(total),
            })
        return labours

    def _get_bom(self, bom_id=False, product_id=False, line_qty=False, line_id=False, level=False):
        bom = self.env['mrp.bom'].browse(bom_id)
        company = bom.company_id or self.env.company
        bom_quantity = line_qty
        if line_id:
            current_line = self.env['mrp.bom.line'].browse(int(line_id))
            bom_quantity = current_line.product_uom_id._compute_quantity(line_qty, bom.product_uom_id) or 0
        # Display bom components for current selected product variant
        if product_id:
            product = self.env['product.product'].browse(int(product_id))
        else:
            product = bom.product_id or bom.product_tmpl_id.product_variant_id
        if product:
            components, total = self._get_bom_lines(bom, bom_quantity, product, line_id, level)
            price = total
            attachments = self.env['mrp.document'].search(['|', '&', ('res_model', '=', 'product.product'),
            ('res_id', '=', product.id), '&', ('res_model', '=', 'product.template'), ('res_id', '=', product.product_tmpl_id.id)])
        else:
            # Use the product template instead of the variant
            price = bom.product_tmpl_id.uom_id._compute_price(bom.product_tmpl_id.with_company(company).standard_price, bom.product_uom_id) * bom_quantity
            attachments = self.env['mrp.document'].search([('res_model', '=', 'product.template'), ('res_id', '=', bom.product_tmpl_id.id)])
        operations = self._get_operation_line(product, bom, float_round(bom_quantity, precision_rounding=1, rounding_method='UP'), 0)

        materials = self._get_material_line(bom)
        labours = self._get_direct_labour_line(bom)
        overheads = self._get_direct_oh_line(bom)
        lines = {
            'bom': bom,
            'bom_qty': bom_quantity,
            'bom_prod_name': product.display_name,
            'currency': company.currency_id,
            'product': product,
            'code': bom and bom.display_name or '',
            'price': price,
            'total': sum([op['total'] for op in operations]),
            'level': level or 0,
            'operations': operations,
            'materials': materials,
            'total_materials': sum([m['duration_expected'] for m in materials]),
            'cost_materials':sum([m['total'] for m in materials]),
            'total_labours': sum([l['duration_expected'] for l in labours]),
            'cost_labours': sum([l['total'] for l in labours]),
            'total_ohs': sum([l['duration_expected'] for l in overheads]),
            'cost_ohs': sum([l['total'] for l in overheads]),
            'operations_cost': sum([op['total'] for op in operations]),
            'attachments': attachments,
            'operations_time': sum([op['duration_expected'] for op in operations])
        }
        components, total = self._get_bom_lines(bom, bom_quantity, product, line_id, level)
        lines['total'] += total
        lines['components'] = components
        byproducts, byproduct_cost_portion = self._get_byproducts_lines(bom, bom_quantity, level, lines['total'])
        lines['byproducts'] = byproducts
        lines['cost_share'] = float_round(1 - byproduct_cost_portion, precision_rounding=0.0001)
        lines['bom_cost'] = lines['total'] * lines['cost_share']
        lines['byproducts_cost'] = sum(byproduct['bom_cost'] for byproduct in byproducts)
        lines['byproducts_total'] = sum(byproduct['product_qty'] for byproduct in byproducts)
        lines['extra_column_count'] = self._get_extra_column_count()
        return lines
