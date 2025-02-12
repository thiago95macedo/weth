# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
from odoo import fields, models


class DocumentSupplement(models.Model):
    _name = "l10n_br_fiscal.document.supplement"
    _description = "Document Supplement Data"

    qrcode = fields.Char(string="QR Code")

    url_key = fields.Char(string="QR Code URL Key")
