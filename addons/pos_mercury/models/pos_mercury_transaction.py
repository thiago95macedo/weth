from datetime import date, timedelta

import requests

from html import unescape

from odoo import models, api, service
from odoo.tools.translate import _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, misc


class MercuryTransaction(models.Model):
    _name = 'pos_mercury.mercury_transaction'
    _description = 'Point of Sale Vantiv Transaction'

    def _get_pos_session(self):
        pos_session = self.env['pos.session'].search([('state', '=', 'opened'), ('user_id', '=', self.env.uid)], limit=1)
        if not pos_session:
            raise UserError(_("No opened point of sale session for user %s found.", self.env.user.name))

        pos_session.login()

        return pos_session

    def _get_pos_mercury_config_id(self, config, payment_method_id):
        payment_method = config.current_session_id.payment_method_ids.filtered(lambda pm: pm.id == payment_method_id)

        if payment_method and payment_method.pos_mercury_config_id:
            return payment_method.pos_mercury_config_id
        else:
            raise UserError(_("No Vantiv configuration associated with the payment method."))

    def _setup_request(self, data):
        # todo: in master make the client include the pos.session id and use that
        pos_session = self._get_pos_session()

        config = pos_session.config_id
        pos_mercury_config = self._get_pos_mercury_config_id(config, data['payment_method_id'])

        data['operator_id'] = pos_session.user_id.login
        data['merchant_id'] = pos_mercury_config.sudo().merchant_id
        data['merchant_pwd'] = pos_mercury_config.sudo().merchant_pwd
        data['memo'] = "Odoo " + service.common.exp_version()['server_version']

    def _do_request(self, template, data):
        xml_transaction = self.env.ref(template)._render(data).decode()

        if not data['merchant_id'] or not data['merchant_pwd']:
            return "not setup"

        soap_header = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:mer="http://www.mercurypay.com"><soapenv:Header/><soapenv:Body><mer:CreditTransaction><mer:tran>'
        soap_footer = '</mer:tran><mer:pw>' + data['merchant_pwd'] + '</mer:pw></mer:CreditTransaction></soapenv:Body></soapenv:Envelope>'
        xml_transaction = soap_header + misc.html_escape(xml_transaction) + soap_footer

        response = ''

        headers = {
            'Content-Type': 'text/xml',
            'SOAPAction': 'http://www.mercurypay.com/CreditTransaction',
        }

        url = 'https://w1.mercurypay.com/ws/ws.asmx'
        if self.env['ir.config_parameter'].sudo().get_param('pos_mercury.enable_test_env'):
            url = 'https://w1.mercurycert.net/ws/ws.asmx'

        try:
            r = requests.post(url, data=xml_transaction, headers=headers, timeout=65)
            r.raise_for_status()
            response = unescape(r.content.decode())
        except Exception:
            response = "timeout"

        return response

    def _do_reversal_or_voidsale(self, data, is_voidsale):
        try:
            self._setup_request(data)
        except UserError:
            return "internal error"

        data['is_voidsale'] = is_voidsale
        response = self._do_request('pos_mercury.mercury_voidsale', data)
        return response

    @api.model
    def do_payment(self, data):
        try:
            self._setup_request(data)
        except UserError:
            return "internal error"

        response = self._do_request('pos_mercury.mercury_transaction', data)
        return response

    @api.model
    def do_reversal(self, data):
        return self._do_reversal_or_voidsale(data, False)

    @api.model
    def do_voidsale(self, data):
        return self._do_reversal_or_voidsale(data, True)

    def do_return(self, data):
        try:
            self._setup_request(data)
        except UserError:
            return "internal error"

        response = self._do_request('pos_mercury.mercury_return', data)
        return response

