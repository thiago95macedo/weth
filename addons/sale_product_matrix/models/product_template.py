from odoo import api, models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_add_mode = fields.Selection([
        ('configurator', 'Product Configurator'),
        ('matrix', 'Order Grid Entry'),
    ], string='Add product mode', default='configurator', help="Configurator: choose attribute values to add the matching \
        product variant to the order.\nGrid: add several variants at once from the grid of attribute values")

    def get_single_product_variant(self):
        res = super(ProductTemplate, self).get_single_product_variant()
        if self.has_configurable_attributes:
            res['mode'] = self.product_add_mode
        else:
            res['mode'] = 'configurator'
        return res
