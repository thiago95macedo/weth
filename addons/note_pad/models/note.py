from odoo import fields, models


class NotePad(models.Model):

    _name = 'note.note'
    _inherit = ['pad.common', 'note.note']

    _pad_fields = ['note_pad']

    note_pad_url = fields.Char('Pad Url', pad_content_field='memo', copy=False)
