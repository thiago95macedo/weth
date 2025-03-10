from odoo.addons.test_mass_mailing.tests.common import TestMassMailCommon
from odoo.tests.common import users
from odoo.tools import mute_logger


class TestMailingTest(TestMassMailCommon):

    @users('user_marketing')
    @mute_logger('odoo.addons.mail.models.mail_render_mixin')
    def test_mailing_test_button(self):
        mailing = self.env['mailing.mailing'].create({
            'name': 'TestButton',
            'subject': 'Subject ${object.name}',
            'preview': 'Preview ${object.name}',
            'state': 'draft',
            'mailing_type': 'mail',
            'body_html': '<p>Hello ${object.name}</p>',
            'mailing_model_id': self.env['ir.model']._get('res.partner').id,
        })
        mailing_test = self.env['mailing.mailing.test'].create({
            'email_to': 'test@test.com',
            'mass_mailing_id': mailing.id,
        })

        with self.mock_mail_gateway():
            mailing_test.send_mail_test()

        # Test if bad jinja in the subject raises an error
        mailing.write({'subject': 'Subject ${object.name_id.id}'})
        with self.mock_mail_gateway(), self.assertRaises(Exception):
            mailing_test.send_mail_test()

        # Test if bad jinja in the body raises an error
        mailing.write({
            'subject': 'Subject ${object.name}',
            'body_html': '<p>Hello ${object.name_id.id}</p>',
        })
        with self.mock_mail_gateway(), self.assertRaises(Exception):
            mailing_test.send_mail_test()

        # Test if bad jinja in the preview raises an error
        mailing.write({
            'body_html': '<p>Hello ${object.name}</p>',
            'preview': 'Preview ${object.name_id.id}',
        })
        with self.mock_mail_gateway(), self.assertRaises(Exception):
            mailing_test.send_mail_test()
