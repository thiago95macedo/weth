from odoo import models, _


class Event(models.Model):
    _inherit = "event.event"

    def action_mass_mailing_attendees(self):
        return {
            'name': 'Mass Mail Attendees',
            'type': 'ir.actions.act_window',
            'res_model': 'mailing.mailing',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_mailing_model_id': self.env.ref('event.model_event_registration').id,
                'default_mailing_domain': repr([('event_id', 'in', self.ids), ('state', '!=', 'cancel')])
            },
        }

    def action_invite_contacts(self):
        return {
            'name': 'Mass Mail Invitation',
            'type': 'ir.actions.act_window',
            'res_model': 'mailing.mailing',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_mailing_model_id': self.env.ref('base.model_res_partner').id},
        }
