# coding: utf-8
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    adyen_ask_customer_for_tip = fields.Boolean('Ask Customers For Tip', help='Prompt the customer to tip.')

    @api.onchange('iface_tipproduct')
    def _onchange_iface_tipproduct_adyen(self):
        if not self.iface_tipproduct:
            self.adyen_ask_customer_for_tip = False

    @api.constrains('adyen_ask_customer_for_tip', 'iface_tipproduct', 'tip_product_id')
    def _check_adyen_ask_customer_for_tip(self):
        for config in self:
            if config.adyen_ask_customer_for_tip and (not config.tip_product_id or not config.iface_tipproduct):
                raise ValidationError(_("Please configure a tip product for POS %s to support tipping with Adyen.", config.name))
