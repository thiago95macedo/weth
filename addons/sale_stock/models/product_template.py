from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.onchange('type')
    def _onchange_type(self):
        """ We want to prevent storable product to be expensed, since it make no sense as when confirm
            expenses, the product is already out of our stock.
        """
        res = super(ProductTemplate, self)._onchange_type()
        if self.type == 'product':
            self.expense_policy = 'no'
            self.service_type = 'manual'
        return res
