from odoo import fields, models


class ModelA(models.Model):
    _name = "test_rpc.model_a"
    _description = "Model A"

    name = fields.Char(required=True)
    field_b1 = fields.Many2one("test_rpc.model_b", string="required field", required=True)
    field_b2 = fields.Many2one("test_rpc.model_b", string="restricted field", ondelete="restrict")


class ModelB(models.Model):
    _name = "test_rpc.model_b"
    _description = "Model B"

    name = fields.Char(required=True)
