from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pad_server = fields.Char(related='company_id.pad_server', string="Pad Server", readonly=False)
    pad_key = fields.Char(related='company_id.pad_key', string="Pad API Key", readonly=False)
