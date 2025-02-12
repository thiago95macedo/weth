from odoo import models


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        res = super(Http, self).session_info()
        if self.env.user.has_group('base.group_user'):
            res['odoobot_initialized'] = self.env.user.odoobot_state not in [False, 'not_initialized']
        return res
