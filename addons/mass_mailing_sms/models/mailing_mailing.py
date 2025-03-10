import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class Mailing(models.Model):
    _inherit = 'mailing.mailing'

    @api.model
    def default_get(self, fields):
        res = super(Mailing, self).default_get(fields)
        if fields is not None and 'keep_archives' in fields and res.get('mailing_type') == 'sms':
            res['keep_archives'] = True
        return res

    # mailing options
    mailing_type = fields.Selection(selection_add=[
        ('sms', 'SMS')
    ], ondelete={'sms': 'set default'})

    # 'sms_subject' added to override 'subject' field (string attribute should be labelled "Title" when mailing_type == 'sms').
    # 'sms_subject' should have the same helper as 'subject' field when 'mass_mailing_sms' installed.
    # otherwise 'sms_subject' will get the old helper from 'mass_mailing' module.
    # overriding 'subject' field helper in this model is not working, since the helper will keep the new value
    # even when 'mass_mailing_sms' removed (see 'mailing_mailing_view_form_sms' for more details).                    
    sms_subject = fields.Char('Title', help='For an email, the subject your recipients will see in their inbox.\n'
                              'For an SMS, the internal title of the message.',
                              related='subject', translate=True, readonly=False)
    # sms options
    body_plaintext = fields.Text('SMS Body', compute='_compute_body_plaintext', store=True, readonly=False)
    sms_template_id = fields.Many2one('sms.template', string='SMS Template', ondelete='set null')
    sms_has_insufficient_credit = fields.Boolean(
        'Insufficient IAP credits', compute='_compute_sms_has_iap_failure',
        help='UX Field to propose to buy IAP credits')
    sms_has_unregistered_account = fields.Boolean(
        'Unregistered IAP account', compute='_compute_sms_has_iap_failure',
        help='UX Field to propose to Register the SMS IAP account')
    sms_force_send = fields.Boolean(
        'Send Directly', help='Use at your own risks.')
    # opt_out_link
    sms_allow_unsubscribe = fields.Boolean('Include opt-out link', default=False)

    @api.depends('mailing_type')
    def _compute_medium_id(self):
        super(Mailing, self)._compute_medium_id()
        for mailing in self:
            if mailing.mailing_type == 'sms' and (not mailing.medium_id or mailing.medium_id == self.env.ref('utm.utm_medium_email')):
                mailing.medium_id = self.env.ref('mass_mailing_sms.utm_medium_sms').id
            elif mailing.mailing_type == 'mail' and (not mailing.medium_id or mailing.medium_id == self.env.ref('mass_mailing_sms.utm_medium_sms')):
                mailing.medium_id = self.env.ref('utm.utm_medium_email').id

    @api.depends('sms_template_id', 'mailing_type')
    def _compute_body_plaintext(self):
        for mailing in self:
            if mailing.mailing_type == 'sms' and mailing.sms_template_id:
                mailing.body_plaintext = mailing.sms_template_id.body

    @api.depends('mailing_trace_ids.failure_type')
    def _compute_sms_has_iap_failure(self):
        failures = ['sms_acc', 'sms_credit'] 
        if not self.ids:
            self.sms_has_insufficient_credit = self.sms_has_unregistered_account = False
        else:
            traces = self.env['mailing.trace'].sudo().read_group([
                        ('mass_mailing_id', 'in', self.ids),
                        ('trace_type', '=', 'sms'),
                        ('failure_type', 'in', failures)
            ], ['mass_mailing_id', 'failure_type'], ['mass_mailing_id', 'failure_type'], lazy=False)

            trace_dict = dict.fromkeys(self.ids, {key: False for key in failures})
            for t in traces:
                trace_dict[t['mass_mailing_id'][0]][t['failure_type']] =  t['__count'] and True or False

            for mail in self:
                mail.sms_has_insufficient_credit = trace_dict[mail.id]['sms_credit']
                mail.sms_has_unregistered_account = trace_dict[mail.id]['sms_acc']


    # --------------------------------------------------
    # ORM OVERRIDES
    # --------------------------------------------------

    @api.model
    def create(self, values):
        # Get subject from "sms_subject" field when SMS installed (used to build the name of record in the super 'create' method)
        if values.get('mailing_type') == 'sms' and values.get('sms_subject'):
            values['subject'] = values['sms_subject']
        return super(Mailing, self).create(values)

    # --------------------------------------------------
    # BUSINESS / VIEWS ACTIONS
    # --------------------------------------------------

    def action_put_in_queue_sms(self):
        res = self.action_put_in_queue()
        if self.sms_force_send:
            self.action_send_mail()
        return res

    def action_send_now_sms(self):
        if not self.sms_force_send:
            self.write({'sms_force_send': True})
        return self.action_send_mail()

    def action_retry_failed(self):
        mass_sms = self.filtered(lambda m: m.mailing_type == 'sms')
        if mass_sms:
            mass_sms.action_retry_failed_sms()
        return super(Mailing, self - mass_sms).action_retry_failed()

    def action_retry_failed_sms(self):
        failed_sms = self.env['sms.sms'].sudo().search([
            ('mailing_id', 'in', self.ids),
            ('state', '=', 'error')
        ])
        failed_sms.mapped('mailing_trace_ids').unlink()
        failed_sms.unlink()
        self.write({'state': 'in_queue'})

    def action_test(self):
        if self.mailing_type == 'sms':
            ctx = dict(self.env.context, default_mailing_id=self.id)
            return {
                'name': _('Test SMS marketing'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mailing.sms.test',
                'target': 'new',
                'context': ctx,
            }
        return super(Mailing, self).action_test()

    def _action_view_traces_filtered(self, view_filter):
        action = super(Mailing, self)._action_view_traces_filtered(view_filter)
        if self.mailing_type == 'sms':
            action['views'] = [(self.env.ref('mass_mailing_sms.mailing_trace_view_tree_sms').id, 'tree'),
                               (self.env.ref('mass_mailing_sms.mailing_trace_view_form_sms').id, 'form')]
        return action

    def action_buy_sms_credits(self):
        url = self.env['iap.account'].get_credits_url(service_name='sms')
        return {
            'type': 'ir.actions.act_url',
            'url': url,
        }

    # --------------------------------------------------
    # SMS SEND
    # --------------------------------------------------

    def _get_opt_out_list_sms(self):
        """Returns a set of emails opted-out in target model"""
        self.ensure_one()
        opt_out = []
        target = self.env[self.mailing_model_real]
        if self.mailing_model_real == 'mailing.contact':
            # if user is opt_out on One list but not on another
            # or if two user with same email address, one opted in and the other one opted out, send the mail anyway
            # TODO DBE Fixme : Optimise the following to get real opt_out and opt_in
            subscriptions = self.env['mailing.contact.subscription'].sudo().search(
                [('list_id', 'in', self.contact_list_ids.ids)])
            opt_out_contacts = subscriptions.filtered(lambda sub: sub.opt_out).mapped('contact_id')
            opt_in_contacts = subscriptions.filtered(lambda sub: not sub.opt_out).mapped('contact_id')
            opt_out = list(set(c.id for c in opt_out_contacts if c not in opt_in_contacts))

            _logger.info("Mass SMS %s targets %s: optout: %s contacts", self, target._name, len(opt_out))
        else:
            _logger.info("Mass SMS %s targets %s: no opt out list available", self, target._name)
        return opt_out

    def _get_seen_list_sms(self):
        """Returns a set of emails already targeted by current mailing/campaign (no duplicates)"""
        self.ensure_one()
        target = self.env[self.mailing_model_real]

        partner_fields = []
        if isinstance(target, self.pool['mail.thread.phone']):
            phone_fields = ['phone_sanitized']
        elif isinstance(target, self.pool['mail.thread']):
            phone_fields = [
                fname for fname in target._sms_get_number_fields()
                if fname in target._fields and target._fields[fname].store
            ]
            partner_fields = target._sms_get_partner_fields()
        else:
            phone_fields = []
            if 'mobile' in target._fields and target._fields['mobile'].store:
                phone_fields.append('mobile')
            if 'phone' in target._fields and target._fields['phone'].store:
                phone_fields.append('phone')
        partner_field = next(
            (fname for fname in partner_fields if target._fields[fname].store and target._fields[fname].type == 'many2one'),
            False
        )
        if not phone_fields and not partner_field:
            raise UserError(_("Unsupported %s for mass SMS", self.mailing_model_id.name))

        query = """
            SELECT %(select_query)s
              FROM mailing_trace trace
              JOIN %(target_table)s target ON (trace.res_id = target.id)
              %(join_add_query)s
             WHERE (%(where_query)s)
               AND trace.mass_mailing_id = %%(mailing_id)s
               AND trace.model = %%(target_model)s
        """
        if phone_fields:
            # phone fields are checked on target mailed model
            select_query = 'target.id, ' + ', '.join('target.%s' % fname for fname in phone_fields)
            where_query = ' OR '.join('target.%s IS NOT NULL' % fname for fname in phone_fields)
            join_add_query = ''
        else:
            # phone fields are checked on res.partner model
            partner_phone_fields = ['mobile', 'phone']
            select_query = 'target.id, ' + ', '.join('partner.%s' % fname for fname in partner_phone_fields)
            where_query = ' OR '.join('partner.%s IS NOT NULL' % fname for fname in partner_phone_fields)
            join_add_query = 'JOIN res_partner partner ON (target.%s = partner.id)' % partner_field

        query = query % {
            'select_query': select_query,
            'where_query': where_query,
            'target_table': target._table,
            'join_add_query': join_add_query,
        }
        params = {'mailing_id': self.id, 'target_model': self.mailing_model_real}
        self._cr.execute(query, params)
        query_res = self._cr.fetchall()
        seen_list = set(number for item in query_res for number in item[1:] if number)
        seen_ids = set(item[0] for item in query_res)
        _logger.info("Mass SMS %s targets %s: already reached %s SMS", self, target._name, len(seen_list))
        return list(seen_ids), list(seen_list)

    def _send_sms_get_composer_values(self, res_ids):
        return {
            # content
            'body': self.body_plaintext,
            'template_id': self.sms_template_id.id,
            'res_model': self.mailing_model_real,
            'res_ids': repr(res_ids),
            # options
            'composition_mode': 'mass',
            'mailing_id': self.id,
            'mass_keep_log': self.keep_archives,
            'mass_force_send': self.sms_force_send,
            'mass_sms_allow_unsubscribe': self.sms_allow_unsubscribe,
        }

    def action_send_mail(self, res_ids=None):
        mass_sms = self.filtered(lambda m: m.mailing_type == 'sms')
        if mass_sms:
            mass_sms.action_send_sms(res_ids=res_ids)
        return super(Mailing, self - mass_sms).action_send_mail(res_ids=res_ids)

    def action_send_sms(self, res_ids=None):
        for mailing in self:
            if not res_ids:
                res_ids = mailing._get_remaining_recipients()
            if not res_ids:
                raise UserError(_('There are no recipients selected.'))

            composer = self.env['sms.composer'].with_context(active_id=False).create(mailing._send_sms_get_composer_values(res_ids))
            composer._action_send_sms()
            mailing.write({'state': 'done', 'sent_date': fields.Datetime.now()})
        return True

    # --------------------------------------------------
    # TOOLS
    # --------------------------------------------------

    def _get_default_mailing_domain(self):
        mailing_domain = super(Mailing, self)._get_default_mailing_domain()
        if self.mailing_type == 'sms' and 'phone_sanitized_blacklisted' in self.env[self.mailing_model_name]._fields:
            mailing_domain = expression.AND([mailing_domain, [('phone_sanitized_blacklisted', '=', False)]])

        return mailing_domain
