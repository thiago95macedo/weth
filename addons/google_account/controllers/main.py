import json
from werkzeug.exceptions import BadRequest
from werkzeug.utils import redirect

from odoo import http, registry
from odoo.http import request


class GoogleAuth(http.Controller):

    @http.route('/google_account/authentication', type='http', auth="public")
    def oauth2callback(self, **kw):
        """ This route/function is called by Google when user Accept/Refuse the consent of Google """
        state = json.loads(kw.get('state', '{}'))
        dbname = state.get('d')
        service = state.get('s')
        url_return = state.get('f')
        base_url = request.httprequest.url_root.strip('/')
        if (not dbname or not service or (kw.get('code') and not url_return)):
            raise BadRequest()

        with registry(dbname).cursor() as cr:
            if kw.get('code'):
                access_token, refresh_token, ttl = request.env['google.service'].with_context(base_url=base_url)._get_google_tokens(kw['code'], service)
                # LUL TODO only defined in google_calendar
                request.env.user._set_auth_tokens(access_token, refresh_token, ttl)
                return redirect(url_return)
            elif kw.get('error'):
                return redirect("%s%s%s" % (url_return, "?error=", kw['error']))
            else:
                return redirect("%s%s" % (url_return, "?error=Unknown_error"))
