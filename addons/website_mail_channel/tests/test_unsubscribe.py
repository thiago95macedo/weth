from odoo.tests import common, tagged
from odoo.tools.misc import mute_logger, ustr


@tagged('-at_install', 'post_install')
class TestConfirmUnsubscribe(common.HttpCase):
    def setUp(self):
        super(TestConfirmUnsubscribe, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Bob',
            'email': 'bob@bob.bob'
        })
        self.mailing_list = self.env['mail.channel'].create({
            'name': 'Test Mailing List',
            'public': 'public',
        })
        self.token = self.mailing_list._generate_action_token(self.partner.id, action='unsubscribe')

    def test_not_subscribed(self):
        """Test warning works"""
        self._unsubscribe_check("The address %s is already unsubscribed" % self.partner.email)

    @mute_logger('odoo.addons.website.models.ir_ui_view')
    def test_not_subscribed_no_template(self):
        """ Test warning works on db without template (code update w/o module update) """
        self.env.ref('website_mail_channel.not_subscribed').unlink()
        self.assertEqual(
            self.env['ir.model.data'].search_count([
            ('module', '=', 'website_mail_channel'),
            ('name', '=', 'not_subscribed'),
        ]), 0, 'XID for template should have been deleted')

        self._unsubscribe_check("The address %s is already unsubscribed or was never subscribed to any mailing list" % self.partner.email)

    def test_wrong_token(self):
        self.mailing_list.sudo().write({
            'channel_partner_ids': [(4, self.partner.id, False)]
        })
        self.token = 'XXX'

        self._unsubscribe_check("Invalid or expired confirmation link.")

    def test_successful_unsubscribe(self):
        self.mailing_list.sudo().write({
            'channel_partner_ids': [(4, self.partner.id, False)]
        })

        self._unsubscribe_check("You have been correctly unsubscribed")

    def _unsubscribe_check(self, text):
        url = "/groups/unsubscribe/{}/{}/{}".format(
            self.mailing_list.id, self.partner.id,
            self.token
        )
        r = self.url_open(url)
        body = ustr(r.content)
        # normalize space to make matching simpler
        self.assertIn(text, u' '.join(body.split()))
