from odoo import fields, models

class SomeObj(models.Model):
    _name = 'test_access_right.some_obj'
    _description = 'Object For Test Access Right'

    val = fields.Integer()
    categ_id = fields.Many2one('test_access_right.obj_categ')
    company_id = fields.Many2one('res.company')
    forbidden = fields.Integer(
        groups='test_access_rights.test_group,!base.group_no_one,base.group_user,!base.group_public',
        default=5
    )
    forbidden2 = fields.Integer(groups='test_access_rights.test_group')
    forbidden3 = fields.Integer(groups=fields.NO_ACCESS)

class Container(models.Model):
    _name = 'test_access_right.container'
    _description = 'Test Access Right Container'

    some_ids = fields.Many2many('test_access_right.some_obj', 'test_access_right_rel', 'container_id', 'some_id')

class Parent(models.Model):
    _name = 'test_access_right.parent'
    _description = 'Object for testing related access rights'

    _inherits = {'test_access_right.some_obj': 'obj_id'}

    obj_id = fields.Many2one('test_access_right.some_obj', required=True, ondelete='restrict')

class ObjCateg(models.Model):
    _name = 'test_access_right.obj_categ'
    _description = "Context dependent searchable model"

    name = fields.Char(required=True)

    def search(self, args, **kwargs):
        if self.env.context.get('only_media'):
            args += [('name', '=', 'Media')]
        return super(ObjCateg, self).search(args, **kwargs)


class FakeTicket(models.Model):
    """We want to simulate a record that would typically be accessed by a portal user,
       with a relational field to records that could not be accessed by a portal user.
    """
    _name = 'test_access_right.ticket'
    _description = 'Fake ticket For Test Access Right'

    name = fields.Char()
    message_partner_ids = fields.Many2many(comodel_name='res.partner')


class ResPartner(models.Model):
    """User inherits partner, so we are implicitly adding these fields to User
       This essentially reproduces the (sad) situation introduced by account.
    """
    _name = 'res.partner'
    _inherit = 'res.partner'

    currency_id = fields.Many2one('res.currency', compute='_get_company_currency', readonly=True)
    monetary = fields.Monetary()  # implicitly depends on currency_id as currency_field

    def _get_company_currency(self):
        for partner in self:
            partner.currency_id = partner.sudo().company_id.currency_id
