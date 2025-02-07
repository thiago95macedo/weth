# Copyright 2022 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated by https://github.com/akretion/xsdata-odoo
#
import textwrap
from odoo import fields, models

__NAMESPACE__ = "http://tempuri.org/PurchaseOrderSchema.xsd"


class Items(models.AbstractModel):
    _description = "Items"
    _name = "poxsd.10.items"
    _inherit = "spec.mixin.poxsd"
    _binding_type = "Items"

    
    poxsd10_item = fields.One2many("poxsd.10.item", "poxsd10_item_Items_id", 
        string="item"
    )


class Item(models.AbstractModel):
    _description = "item"
    _name = "poxsd.10.item"
    _inherit = "spec.mixin.poxsd"
    _binding_type = "Items.Item"

    poxsd10_item_Items_id = fields.Many2one(
        comodel_name="poxsd.10.items",
        xsd_implicit=True,
        ondelete="cascade"
    )
    poxsd10_productName = fields.Float(
        xsd_required=True,
        string="productName"
    )
    poxsd10_quantity = fields.Integer(
        xsd_required=True,
        string="quantity"
    )
    poxsd10_USPrice = fields.Float(
        xsd_type="xsd:decimal",
        xsd_required=True,
        string="USPrice"
    )
    poxsd10_comment = fields.Float(
        xsd_required=True,
        string="comment"
    )
    poxsd10_shipDate = fields.Float(
        string="shipDate"
    )
    poxsd10_partNum = fields.Float(
        xsd_type="tns:SKU",
        string="partNum"
    )


class Usaddress(models.AbstractModel):
    "Purchase order schema for Example.Microsoft.com."
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = "poxsd.10.usaddress"
    _inherit = "spec.mixin.poxsd"
    _binding_type = "Usaddress"

    
    poxsd10_name = fields.Float(
        xsd_required=True,
        string="name"
    )
    poxsd10_street = fields.Float(
        xsd_required=True,
        string="street"
    )
    poxsd10_city = fields.Float(
        xsd_required=True,
        string="city"
    )
    poxsd10_state = fields.Float(
        xsd_required=True,
        string="state"
    )
    poxsd10_zip = fields.Float(
        xsd_type="xsd:decimal",
        xsd_required=True,
        string="zip"
    )
    poxsd10_country = fields.Float(
        xsd_type="xsd:NMTOKEN",
        string="country"
    )


class Comment(models.AbstractModel):
    _description = "comment"
    _name = "poxsd.10.comment"
    _inherit = "spec.mixin.poxsd"
    _binding_type = "Comment"

    
    poxsd10_value = fields.Float(
        xsd_required=True,
        string="value"
    )


class PurchaseOrderType(models.AbstractModel):
    _description = "PurchaseOrderType"
    _name = "poxsd.10.purchaseordertype"
    _inherit = "spec.mixin.poxsd"
    _binding_type = "PurchaseOrderType"

    
    poxsd10_shipTo = fields.Many2one(
        xsd_type="tns:USAddress",
        xsd_required=True,
        string="shipTo",
        comodel_name="poxsd.10.usaddress"
    )
    poxsd10_billTo = fields.Many2one(
        xsd_type="tns:USAddress",
        xsd_required=True,
        string="billTo",
        comodel_name="poxsd.10.usaddress"
    )
    poxsd10_comment = fields.Float(
        string="comment"
    )
    poxsd10_items = fields.Many2one(
        xsd_type="tns:Items",
        xsd_required=True,
        string="items",
        comodel_name="poxsd.10.items"
    )
    poxsd10_orderDate = fields.Float(
        string="orderDate"
    )
    poxsd10_confirmDate = fields.Float(
        xsd_required=True,
        string="confirmDate"
    )


class PurchaseOrder(models.AbstractModel):
    _description = "purchaseOrder"
    _name = "poxsd.10.purchaseorder"
    _inherit = "spec.mixin.poxsd"
    _binding_type = "PurchaseOrder"
