from odoo import api, SUPERUSER_ID

from . import models
from . import controllers
from . import wizards


def reset_payment_provider(cr, registry, provider):
    env = api.Environment(cr, SUPERUSER_ID, {})
    acquirers = env['payment.acquirer'].search([('provider', '=', provider)])
    acquirers.write({
        'view_template_id': acquirers._get_default_view_template_id().id,
        'provider': 'manual',
        'state': 'disabled',
    })
