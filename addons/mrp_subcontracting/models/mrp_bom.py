from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.osv.expression import AND

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    type = fields.Selection(selection_add=[
        ('subcontract', 'Subcontracting')
    ], ondelete={'subcontract': lambda recs: recs.write({'type': 'normal', 'active': False})})
    subcontractor_ids = fields.Many2many('res.partner', 'mrp_bom_subcontractor', string='Subcontractors', check_company=True)

    def _bom_subcontract_find(self, product_tmpl=None, product=None, picking_type=None, company_id=False, bom_type='subcontract', subcontractor=False):
        domain = self._bom_find_domain(product_tmpl=product_tmpl, product=product, picking_type=picking_type, company_id=company_id, bom_type=bom_type)
        if subcontractor:
            domain = AND([domain, [('subcontractor_ids', 'parent_of', subcontractor.ids)]])
            return self.search(domain, order='sequence, product_id', limit=1)
        else:
            return self.env['mrp.bom']

    @api.constrains('operation_ids', 'type')
    def _check_subcontracting_no_operation(self):
        if self.filtered_domain([('type', '=', 'subcontract'), ('operation_ids', '!=', False)]):
            raise ValidationError(_('You can not set a Bill of Material with operations as subcontracting.'))
