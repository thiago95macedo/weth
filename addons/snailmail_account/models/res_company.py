from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    invoice_is_snailmail = fields.Boolean(string='Send by Post', default=False)
