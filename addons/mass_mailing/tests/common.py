import datetime
import random
import re
import werkzeug

from odoo.addons.link_tracker.tests.common import MockLinkTracker
from odoo.addons.mail.tests.common import MailCase, MailCommon, mail_new_test_user
from odoo import tools

class MassMailCase(MailCase, MockLinkTracker):

    # ------------------------------------------------------------
    # ASSERTS
    # ------------------------------------------------------------

    def assertMailingStatistics(self, mailing, **kwargs):
        """ Helper to assert mailing statistics fields. As we have many of them
        it helps lessening test asserts. """
        if not kwargs.get('expected'):
            kwargs['expected'] = len(mailing.mailing_trace_ids)
        if not kwargs.get('delivered'):
            kwargs['delivered'] = len(mailing.mailing_trace_ids)
        for fname in ['scheduled', 'expected', 'sent', 'delivered',
                      'opened', 'replied', 'clicked',
                      'ignored', 'failed', 'bounced']:
            self.assertEqual(
                mailing[fname], kwargs.get(fname, 0),
                'Mailing %s statistics failed: got %s instead of %s' % (fname, mailing[fname], kwargs.get(fname, 0))
            )

    def assertMailTraces(self, recipients_info, mailing, records,
                         check_mail=True, sent_unlink=False,
                         author=None, mail_links_info=None):
        """ Check content of traces. Traces are fetched based on a given mailing
        and records. Their content is compared to recipients_info structure that
        holds expected information. Links content may be checked, notably to
        assert shortening or unsubscribe links. Mail.mail records may optionally
        be checked.

        :param recipients_info: list[{
            # TRACE
            'partner': res.partner record (may be empty),
            'email': email used when sending email (may be empty, computed based on partner),
            'state': outgoing / sent / ignored / bounced / exception / opened (sent by default),
            'record: linked record,
            # MAIL.MAIL
            'content': optional content that should be present in mail.mail body_html;
            'email_to_mail': optional email used for the mail, when different from the
              one stored on the trace itself;
            'email_to_recipients': optional, see '_assertMailMail';
            'failure_type': optional failure reason;
            }, { ... }]

        :param mailing: a mailing.mailing record from which traces have been
          generated;
        :param records: records given to mailing that generated traces. It is
          used notably to find traces using their IDs;
        :param check_mail: if True, also check mail.mail records that should be
          linked to traces;
        :param sent_unlink: it True, sent mail.mail are deleted and we check gateway
          output result instead of actual mail.mail records;
        :param mail_links_info: if given, should follow order of ``recipients_info``
          and give details about links. See ``assertLinkShortenedHtml`` helper for
          more details about content to give;
        :param author: author of sent mail.mail;
        """
        # map trace state to email state
        state_mapping = {
            'sent': 'sent',
            'opened': 'sent',  # opened implies something has been sent
            'replied': 'sent',  # replied implies something has been sent
            'ignored': 'cancel',
            'exception': 'exception',
            'canceled': 'cancel',
            'bounced': 'cancel',
        }

        traces = self.env['mailing.trace'].search([
            ('mass_mailing_id', 'in', mailing.ids),
            ('res_id', 'in', records.ids)
        ])
        debug_info = '\n'.join(
            (
                f'Trace: to {t.email} - state {t.state} - res_id {t.res_id}'
                for t in traces
            )
        )

        # ensure trace coherency
        self.assertTrue(all(s.model == records._name for s in traces))
        self.assertEqual(set(s.res_id for s in traces), set(records.ids))

        # check each traces
        if not mail_links_info:
            mail_links_info = [None] * len(recipients_info)
        for recipient_info, link_info, record in zip(recipients_info, mail_links_info, records):
            partner = recipient_info.get('partner', self.env['res.partner'])
            email = recipient_info.get('email')
            email_to_mail = recipient_info.get('email_to_mail') or email
            email_to_recipients = recipient_info.get('email_to_recipients')
            state = recipient_info.get('state', 'sent')
            record = record or recipient_info.get('record')
            content = recipient_info.get('content')
            if email is None and partner:
                email = partner.email_normalized

            recipient_trace = traces.filtered(
                lambda t: (t.email == email or (not email and not t.email)) and \
                          t.state == state and \
                          (t.res_id == record.id if record else True)
            )
            self.assertTrue(
                len(recipient_trace) == 1,
                'MailTrace: email %s (recipient %s, state: %s, record: %s): found %s records (1 expected)\n%s' % (
                    email, partner, state, record,
                    len(recipient_trace), debug_info)
            )
            self.assertTrue(bool(recipient_trace.mail_mail_id_int))
            if 'failure_type' in recipient_info or state in ('ignored', 'exception', 'canceled', 'bounced'):
                self.assertEqual(recipient_trace.failure_type, recipient_info['failure_type'])

            if check_mail:
                if author is None:
                    author = self.env.user.partner_id

                fields_values = {'mailing_id': mailing}
                if recipient_info.get('mail_values'):
                    fields_values.update(recipient_info['mail_values'])
                if 'failure_reason' in recipient_info:
                    fields_values['failure_reason'] = recipient_info['failure_reason']

                # specific for partner: email_formatted is used
                if partner:
                    if state == 'sent' and sent_unlink:
                        self.assertSentEmail(author, [partner])
                    else:
                        self.assertMailMail(
                            partner, state_mapping[state],
                            author=author,
                            content=content,
                            email_to_recipients=email_to_recipients,
                            fields_values=fields_values,
                        )
                # specific if email is False -> could have troubles finding it if several falsy traces
                elif not email and state in ('ignored', 'canceled', 'bounced'):
                    self.assertMailMailWId(
                        recipient_trace.mail_mail_id_int, state_mapping[state],
                        author=author,
                        content=content,
                        email_to_recipients=email_to_recipients,
                        fields_values=fields_values,
                    )
                else:
                    self.assertMailMailWEmails(
                        [email_to_mail], state_mapping[state],
                        author=author,
                        content=content,
                        email_to_recipients=email_to_recipients,
                        fields_values=fields_values,
                    )

            if link_info:
                trace_mail = self._find_mail_mail_wrecord(record)
                for (anchor_id, url, is_shortened, add_link_params) in link_info:
                    link_params = {'utm_medium': 'Email', 'utm_source': mailing.name}
                    if add_link_params:
                        link_params.update(**add_link_params)
                    self.assertLinkShortenedHtml(
                        trace_mail.body_html,
                        (anchor_id, url, is_shortened),
                        link_params=link_params,
                    )

    # ------------------------------------------------------------
    # TOOLS
    # ------------------------------------------------------------

    def gateway_mail_bounce(self, mailing, record, bounce_base_values=None):
        """ Generate a bounce at mailgateway level.

        :param mailing: a ``mailing.mailing`` record on which we find a trace
          to bounce;
        :param record: record which should bounce;
        :param bounce_base_values: optional values given to routing;
        """
        trace = mailing.mailing_trace_ids.filtered(
            lambda t: t.model == record._name and t.res_id == record.id
        )

        parsed_bounce_values = {
            'email_from': 'some.email@external.example.com',  # TDE check: email_from -> trace email ?
            'to': 'bounce@test.example.com',  # TDE check: bounce alias ?
            'message_id': tools.generate_tracking_message_id('MailTest'),
            'bounced_partner': self.env['res.partner'].sudo(),
            'bounced_message': self.env['mail.message'].sudo()
        }
        if bounce_base_values:
            parsed_bounce_values.update(bounce_base_values)
        parsed_bounce_values.update({
            'bounced_email': trace.email,
            'bounced_msg_id': [trace.message_id],
        })
        self.env['mail.thread']._routing_handle_bounce(False, parsed_bounce_values)
        return trace

    def gateway_mail_click(self, mailing, record, click_label):
        """ Simulate a click on a sent email.

        :param mailing: a ``mailing.mailing`` record on which we find a trace
          to click;
        :param record: record which should click;
        :param click_label: label of link on which we should click;
        """
        trace = mailing.mailing_trace_ids.filtered(
            lambda t: t.model == record._name and t.res_id == record.id
        )

        email = self._find_sent_mail_wemail(trace.email)
        self.assertTrue(bool(email))
        for (_url_href, link_url, _dummy, label) in re.findall(tools.HTML_TAG_URL_REGEX, email['body']):
            if label == click_label and '/r/' in link_url:  # shortened link, like 'http://localhost:8095/r/LBG/m/53'
                parsed_url = werkzeug.urls.url_parse(link_url)
                path_items = parsed_url.path.split('/')
                code, trace_id = path_items[2], int(path_items[4])
                self.assertEqual(trace.id, trace_id)

                self.env['link.tracker.click'].sudo().add_click(
                    code,
                    ip='100.200.300.%3f' % random.random(),
                    country_code='BE',
                    mailing_trace_id=trace.id
                )
                break
        else:
            raise AssertionError('url %s not found in mailing %s for record %s' % (click_label, mailing, record))
        return trace

    def gateway_mail_open(self, mailing, record):
        """ Simulate opening an email through blank.gif icon access. As we
        don't want to use the whole Http layer just for that we will just
        call 'set_opened()' on trace, until having a better option.

        :param mailing: a ``mailing.mailing`` record on which we find a trace
          to open;
        :param record: record which should open;
        """
        trace = mailing.mailing_trace_ids.filtered(
            lambda t: t.model == record._name and t.res_id == record.id
        )
        mail_mail_id_int = trace.mail_mail_id_int
        self.assertTrue(bool(mail_mail_id_int))
        trace.set_opened(mail_mail_ids=[mail_mail_id_int])
        return trace

    @classmethod
    def _create_bounce_trace(cls, mailing, records, dt=None):
        if dt is None:
            dt = datetime.datetime.now() - datetime.timedelta(days=1)
        return cls._create_traces(mailing, records, bounced=dt)

    @classmethod
    def _create_sent_traces(cls, mailing, records, dt=None):
        if dt is None:
            dt = datetime.datetime.now() - datetime.timedelta(days=1)
        return cls._create_traces(mailing, records, sent=dt)

    @classmethod
    def _create_traces(cls, mailing, records, **values):
        if 'email_normalized' in records:
            fname = 'email_normalized'
        elif 'email_from' in records:
            fname = 'email_from'
        else:
            fname = 'email'
        randomized = random.random()
        traces = cls.env['mailing.trace'].create([
            dict({'mass_mailing_id': mailing.id,
                  'model': record._name,
                  'res_id': record.id,
                  # TDE FIXME: improve this with a mail-enabled heuristics
                  'email': record[fname],
                  'message_id': '<%5f@gilbert.boitempomils>' % randomized,
                 }, **values)
            for record in records
        ])
        return traces

    @classmethod
    def _create_mailing_list(cls):
        """ Shortcut to create mailing lists. Currently hardcoded, maybe evolve
        in a near future. """
        cls.mailing_list_1 = cls.env['mailing.list'].with_context(cls._test_context).create({
            'name': 'List1',
            'contact_ids': [
                (0, 0, {'name': 'Déboulonneur', 'email': 'fleurus@example.com'}),
                (0, 0, {'name': 'Gorramts', 'email': 'gorramts@example.com'}),
                (0, 0, {'name': 'Ybrant', 'email': 'ybrant@example.com'}),
            ]
        })
        cls.mailing_list_2 = cls.env['mailing.list'].with_context(cls._test_context).create({
            'name': 'List2',
            'contact_ids': [
                (0, 0, {'name': 'Gilberte', 'email': 'gilberte@example.com'}),
                (0, 0, {'name': 'Gilberte En Mieux', 'email': 'gilberte@example.com'}),
                (0, 0, {'name': 'Norbert', 'email': 'norbert@example.com'}),
                (0, 0, {'name': 'Ybrant', 'email': 'ybrant@example.com'}),
            ]
        })


class MassMailCommon(MailCommon, MassMailCase):

    @classmethod
    def setUpClass(cls):
        super(MassMailCommon, cls).setUpClass()

        cls.user_marketing = mail_new_test_user(
            cls.env, login='user_marketing',
            groups='base.group_user,base.group_partner_manager,mass_mailing.group_mass_mailing_user',
            name='Martial Marketing', signature='--\nMartial')

        cls.email_reply_to = 'MyCompany SomehowAlias <test.alias@test.mycompany.com>'

        cls.env['base'].flush()
