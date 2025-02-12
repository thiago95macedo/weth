from odoo import fields, models


class TestModel(models.Model):
    """ Add website option in server actions. """

    _name = 'test.model'
    _inherit = ['website.seo.metadata', 'website.published.mixin']
    _description = 'Website Model Test'

    name = fields.Char(required=1)
