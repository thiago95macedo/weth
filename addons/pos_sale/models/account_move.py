from odoo import fields, models, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_invoiced_lot_values(self):
        self.ensure_one()

        lot_values = super(AccountMove, self)._get_invoiced_lot_values()

        if self.state == 'draft':
            return lot_values

        # user may not have access to POS orders, but it's ok if they have
        # access to the invoice
        for order in self.sudo().pos_order_ids:
            for line in order.lines:
                lots = line.pack_lot_ids or False
                if lots:
                    for lot in lots:
                        lot_values.append({
                            'product_name': lot.product_id.name,
                            'quantity': line.qty if lot.product_id.tracking == 'lot' else 1.0,
                            'uom_name': line.product_uom_id.name,
                            'lot_name': lot.lot_name,
                        })

        return lot_values
