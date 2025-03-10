from odoo import fields, models


class User(models.Model):
    _inherit = ['res.users']

    resume_line_ids = fields.One2many(related='employee_id.resume_line_ids', readonly=False)
    employee_skill_ids = fields.One2many(related='employee_id.employee_skill_ids', readonly=False)

    def __init__(self, pool, cr):
        """ Override of __init__ to add access rights.
            Access rights are disabled by default, but allowed
            on some specific fields defined in self.SELF_{READ/WRITE}ABLE_FIELDS.
        """
        hr_skills_fields = [
            'resume_line_ids',
            'employee_skill_ids',
        ]
        init_res = super(User, self).__init__(pool, cr)
        # duplicate list to avoid modifying the original reference
        pool[self._name].SELF_READABLE_FIELDS = pool[self._name].SELF_READABLE_FIELDS + hr_skills_fields
        pool[self._name].SELF_WRITEABLE_FIELDS = pool[self._name].SELF_WRITEABLE_FIELDS + hr_skills_fields
        return init_res
