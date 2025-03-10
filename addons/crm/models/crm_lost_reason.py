from odoo import fields, models, _


class LostReason(models.Model):
    _name = "crm.lost.reason"
    _description = 'Opp. Lost Reason'

    name = fields.Char('Description', required=True, translate=True)
    active = fields.Boolean('Active', default=True)
    leads_count = fields.Integer('Leads Count', compute='_compute_leads_count')

    def _compute_leads_count(self):
        lead_data = self.env['crm.lead'].with_context(active_test=False).read_group([('lost_reason', 'in', self.ids)], ['lost_reason'], ['lost_reason'])
        mapped_data = dict((data['lost_reason'][0], data['lost_reason_count']) for data in lead_data)
        for reason in self:
            reason.leads_count = mapped_data.get(reason.id, 0)

    def action_lost_leads(self):
        return {
            'name': _('Leads'),
            'view_mode': 'tree,form',
            'domain': [('lost_reason', 'in', self.ids)],
            'res_model': 'crm.lead',
            'type': 'ir.actions.act_window',
            'context': {'create': False, 'active_test': False},
        }
