from odoo import api, fields, models, _


class StockMove(models.Model):
    _inherit = "stock.move"

    def _is_returned(self, valued_type):
        if self.unbuild_id:
            return True
        return super()._is_returned(valued_type)

    def _get_src_account(self, accounts_data):
        if not self.unbuild_id:
            return super()._get_src_account(accounts_data)
        else:
            return self.location_dest_id.valuation_out_account_id.id or accounts_data['stock_input'].id

    def _get_dest_account(self, accounts_data):
        if not self.unbuild_id:
            return super()._get_dest_account(accounts_data)
        else:
            return self.location_id.valuation_in_account_id.id or accounts_data['stock_output'].id

    def _filter_anglo_saxon_moves(self, product):
        res = super(StockMove, self)._filter_anglo_saxon_moves(product)
        res += self.filtered(lambda m: m.bom_line_id.bom_id.product_tmpl_id.id == product.product_tmpl_id.id)
        return res

    def _should_force_price_unit(self):
        self.ensure_one()
        return self.picking_type_id.code == 'mrp_operation' or super()._should_force_price_unit()
