from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    goal_ids = fields.One2many('gamification.goal', 'user_id')
    badge_ids = fields.One2many('gamification.badge.user', 'user_id')
