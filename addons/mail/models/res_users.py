from collections import defaultdict

from odoo import _, api, exceptions, fields, models, modules
from odoo.addons.base.models.res_users import is_selection_groups


class Users(models.Model):
    """ Update of res.users class
        - add a preference about sending emails about notifications
        - make a new user follow itself
        - add a welcome message
        - add suggestion preference
        - if adding groups to a user, check mail.channels linked to this user
          group, and the user. This is done by overriding the write method.
    """
    _name = 'res.users'
    _inherit = ['res.users']
    _description = 'Users'

    notification_type = fields.Selection([
        ('email', 'Por E-mails'),
        ('inbox', '`Por Sistema`')],
        'Notification', required=True, default='inbox',
        help="Política para lidar com notificações do Chatter:\n"
             "- Lidar por E-mails: as notificações são enviadas para o seu endereço de e-mail\n"
             "- Lidar no Odoo: as notificações aparecem na sua Caixa de Entrada do WETH")
    # channel-specific: moderation
    is_moderator = fields.Boolean(string='Is moderator', compute='_compute_is_moderator')
    moderation_counter = fields.Integer(string='Moderation count', compute='_compute_moderation_counter')
    moderation_channel_ids = fields.Many2many(
        'mail.channel', 'mail_channel_moderator_rel',
        string='Moderated channels')

    @api.depends('moderation_channel_ids.moderation', 'moderation_channel_ids.moderator_ids')
    def _compute_is_moderator(self):
        moderated = self.env['mail.channel'].search([
            ('id', 'in', self.mapped('moderation_channel_ids').ids),
            ('moderation', '=', True),
            ('moderator_ids', 'in', self.ids)
        ])
        user_ids = moderated.mapped('moderator_ids')
        for user in self:
            user.is_moderator = user in user_ids

    def _compute_moderation_counter(self):
        self._cr.execute("""
SELECT channel_moderator.res_users_id, COUNT(msg.id)
FROM "mail_channel_moderator_rel" AS channel_moderator
JOIN "mail_message" AS msg
ON channel_moderator.mail_channel_id = msg.res_id
    AND channel_moderator.res_users_id IN %s
    AND msg.model = 'mail.channel'
    AND msg.moderation_status = 'pending_moderation'
GROUP BY channel_moderator.res_users_id""", [tuple(self.ids)])
        result = dict(self._cr.fetchall())
        for user in self:
            user.moderation_counter = result.get(user.id, 0)

    def __init__(self, pool, cr):
        """ Override of __init__ to add access rights on notification_email_send
            fields. Access rights are disabled by default, but allowed on some
            specific fields defined in self.SELF_{READ/WRITE}ABLE_FIELDS.
        """
        init_res = super(Users, self).__init__(pool, cr)
        # duplicate list to avoid modifying the original reference
        pool[self._name].SELF_WRITEABLE_FIELDS = list(self.SELF_WRITEABLE_FIELDS)
        pool[self._name].SELF_WRITEABLE_FIELDS.extend(['notification_type'])
        # duplicate list to avoid modifying the original reference
        pool[self._name].SELF_READABLE_FIELDS = list(self.SELF_READABLE_FIELDS)
        pool[self._name].SELF_READABLE_FIELDS.extend(['notification_type'])
        return init_res

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if not values.get('login', False):
                action = self.env.ref('base.action_res_users')
                msg = _("You cannot create a new user from here.\n To create new user please go to configuration panel.")
                raise exceptions.RedirectWarning(msg, action.id, _('Go to the configuration panel'))

        users = super(Users, self).create(vals_list)
        # Auto-subscribe to channels
        self.env['mail.channel'].search([('group_ids', 'in', users.groups_id.ids)])._subscribe_users()
        return users

    def write(self, vals):
        write_res = super(Users, self).write(vals)
        if 'active' in vals and not vals['active']:
            self._unsubscribe_from_channels()
        sel_groups = [vals[k] for k in vals if is_selection_groups(k) and vals[k]]
        if vals.get('groups_id'):
            # form: {'group_ids': [(3, 10), (3, 3), (4, 10), (4, 3)]} or {'group_ids': [(6, 0, [ids]}
            user_group_ids = [command[1] for command in vals['groups_id'] if command[0] == 4]
            user_group_ids += [id for command in vals['groups_id'] if command[0] == 6 for id in command[2]]
            self.env['mail.channel'].search([('group_ids', 'in', user_group_ids)])._subscribe_users()
        elif sel_groups:
            self.env['mail.channel'].search([('group_ids', 'in', sel_groups)])._subscribe_users()
        return write_res

    def unlink(self):
        self._unsubscribe_from_channels()
        return super().unlink()

    def _unsubscribe_from_channels(self):
        """ This method un-subscribes users from private mail channels. Main purpose of this
            method is to prevent sending internal communication to archived / deleted users.
            We do not un-subscribes users from public channels because in most common cases,
            public channels are mailing list (e-mail based) and so users should always receive
            updates from public channels until they manually un-subscribe themselves.
        """
        self.mapped('partner_id.channel_ids').filtered(lambda c: c.public != 'public' and c.channel_type == 'channel').write({
            'channel_partner_ids': [(3, pid) for pid in self.mapped('partner_id').ids]
        })

    @api.model
    def systray_get_activities(self):
        query = """SELECT array_agg(res_id) as res_ids, m.id, count(*),
                    CASE
                        WHEN %(today)s::date - act.date_deadline::date = 0 Then 'today'
                        WHEN %(today)s::date - act.date_deadline::date > 0 Then 'overdue'
                        WHEN %(today)s::date - act.date_deadline::date < 0 Then 'planned'
                    END AS states
                FROM mail_activity AS act
                JOIN ir_model AS m ON act.res_model_id = m.id
                WHERE user_id = %(user_id)s
                GROUP BY m.id, states;
                """
        self.env.cr.execute(query, {
            'today': fields.Date.context_today(self),
            'user_id': self.env.uid,
        })
        activity_data = self.env.cr.dictfetchall()
        records_by_state_by_model = defaultdict(lambda: {"today": set(), "overdue": set(), "planned": set(), "all": set()})
        for data in activity_data:
            records_by_state_by_model[data["id"]][data["states"]] = set(data["res_ids"])
            records_by_state_by_model[data["id"]]["all"] = records_by_state_by_model[data["id"]]["all"] | set(data["res_ids"])
        user_activities = {}
        for model_id in records_by_state_by_model:
            model_dic = records_by_state_by_model[model_id]
            model = self.env["ir.model"].browse(model_id).with_prefetch(tuple(records_by_state_by_model.keys()))
            allowed_records = self.env[model.model].search([("id", "in", tuple(model_dic["all"]))])
            if not allowed_records:
                continue
            module = self.env[model.model]._original_module
            icon = module and modules.module.get_module_icon(module)
            today = len(model_dic["today"] & set(allowed_records.ids))
            overdue = len(model_dic["overdue"] & set(allowed_records.ids))
            user_activities[model.model] = {
                "name": model.name,
                "model": model.model,
                "type": "activity",
                "icon": icon,
                "total_count": today + overdue,
                "today_count": today,
                "overdue_count": overdue,
                "planned_count": len(model_dic["planned"] & set(allowed_records.ids)),
                "actions": [
                    {
                        "icon": "fa-clock-o",
                        "name": "Summary",
                    }
                ],
            }
        return list(user_activities.values())


class res_groups_mail_channel(models.Model):
    """ Update of res.groups class
        - if adding users from a group, check mail.channels linked to this user
          group and subscribe them. This is done by overriding the write method.
    """
    _name = 'res.groups'
    _inherit = 'res.groups'
    _description = 'Access Groups'

    def write(self, vals, context=None):
        write_res = super(res_groups_mail_channel, self).write(vals)
        if vals.get('users'):
            # form: {'group_ids': [(3, 10), (3, 3), (4, 10), (4, 3)]} or {'group_ids': [(6, 0, [ids]}
            user_ids = [command[1] for command in vals['users'] if command[0] == 4]
            user_ids += [id for command in vals['users'] if command[0] == 6 for id in command[2]]
            self.env['mail.channel'].search([('group_ids', 'in', self._ids)])._subscribe_users()
        return write_res
