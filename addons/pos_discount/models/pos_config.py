from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    iface_discount = fields.Boolean(string='Order Discounts', help='Allow the cashier to give discounts on the whole order.')
    discount_pc = fields.Float(string='Discount Percentage', help='The default discount percentage', default=10.0)
    discount_product_id = fields.Many2one('product.product', string='Discount Product',
        domain="[('sale_ok', '=', True)]", help='The product used to model the discount.')

    @api.onchange('company_id','module_pos_discount')
    def _default_discount_product_id(self):
        product = self.env.ref("point_of_sale.product_product_consumable", raise_if_not_found=False)
        self.discount_product_id = product if self.module_pos_discount and product and (not product.company_id or product.company_id == self.company_id) else False

    @api.model
    def _default_discount_value_on_module_install(self):
        configs = self.env['pos.config'].search([])
        open_configs = (
            self.env['pos.session']
            .search(['|', ('state', '!=', 'closed'), ('rescue', '=', True)])
            .mapped('config_id')
        )
        # Do not modify configs where an opened session exists.
        for conf in (configs - open_configs):
            conf._default_discount_product_id()
