import werkzeug

from odoo.addons.mass_mailing.tests.common import MassMailCommon
from odoo.tests.common import HttpCase


class TestMassMailingControllers(MassMailCommon, HttpCase):

    def test_tracking_url_token(self):
        mail_mail = self.env['mail.mail'].create({})

        response = self.url_open(mail_mail._get_tracking_url())
        self.assertEqual(response.status_code, 200)

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = werkzeug.urls.url_join(base_url, 'mail/track/%s/fake_token/blank.gif' % mail_mail.id)

        response = self.url_open(url)
        self.assertEqual(response.status_code, 400)

    def test_mailing_view(self):
        mailing = self.env['mailing.mailing'].create({
            'name': 'TestMailing',
            'subject': 'Test',
            'mailing_type': 'mail',
            'body_html': '<p>Hello ${object.name} ${object.hello}</p>',
            'mailing_model_id': self.env['ir.model']._get('res.partner').id,
        })

        partner_id = self.user_admin.partner_id
        self.authenticate('admin', 'admin')

        url = werkzeug.urls.url_join(mailing.get_base_url(), '/mailing/%s/view?res_id=%s' % (mailing.id, partner_id.id))
        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('${', response.text)
        self.assertIn("<p>Hello %s </p>" % partner_id.name, response.text)
