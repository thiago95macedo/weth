from odoo import models, fields


class Users(models.Model):
    _inherit = 'res.users'

    odoobot_state = fields.Selection(selection_add=[
        ('onboarding_canned', 'Onboarding canned'),
    ], ondelete={'onboarding_canned': lambda users: users.write({'odoobot_state': 'disabled'})})
