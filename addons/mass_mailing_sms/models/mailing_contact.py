from odoo import fields, models


class MailingContact(models.Model):
    _name = 'mailing.contact'
    _inherit = ['mailing.contact', 'mail.thread.phone']

    mobile = fields.Char(string='Mobile')

    def _sms_get_number_fields(self):
        # TDE note: should override _phone_get_number_fields but ok as sms is in dependencies
        return ['mobile']
