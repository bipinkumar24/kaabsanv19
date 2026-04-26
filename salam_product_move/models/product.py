from odoo import models

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _compute_bom_price(self, bom, boms_to_recompute=False, byproduct_bom=False):
        res = super(ProductProduct, self)._compute_bom_price(bom, boms_to_recompute, byproduct_bom)
        return res
