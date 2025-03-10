from odoo import api, fields, models


class SaleOrderCancel(models.TransientModel):
    _inherit = 'sale.order.cancel'

    display_delivery_alert = fields.Boolean('Delivery Alert', compute='_compute_display_delivery_alert')

    @api.depends('order_id')
    def _compute_display_delivery_alert(self):
        for wizard in self:
            wizard.display_delivery_alert = bool(any(picking.state == 'done' for picking in wizard.order_id.picking_ids))
