from collections import defaultdict

from odoo import api, fields, models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _run_buy(self, procurements):
        requisitions_values_by_company = defaultdict(list)
        other_procurements = []
        for procurement, rule in procurements:
            if procurement.product_id.purchase_requisition == 'tenders':
                values = self.env['purchase.requisition']._prepare_tender_values(*procurement)
                values['picking_type_id'] = rule.picking_type_id.id
                requisitions_values_by_company[procurement.company_id.id].append(values)
            else:
                other_procurements.append((procurement, rule))
        for company_id, requisitions_values in requisitions_values_by_company.items():
            self.env['purchase.requisition'].sudo().with_company(company_id).create(requisitions_values)
        return super(StockRule, self)._run_buy(other_procurements)

    def _prepare_purchase_order(self, company_id, origins, values):
        res = super(StockRule, self)._prepare_purchase_order(company_id, origins, values)
        values = values[0]
        res['partner_ref'] = values['supplier'].purchase_requisition_id.name
        res['requisition_id'] = values['supplier'].purchase_requisition_id.id
        if values['supplier'].purchase_requisition_id.currency_id:
            res['currency_id'] = values['supplier'].purchase_requisition_id.currency_id.id
        return res

    def _make_po_get_domain(self, company_id, values, partner):
        domain = super(StockRule, self)._make_po_get_domain(company_id, values, partner)
        if 'supplier' in values and values['supplier'].purchase_requisition_id:
            domain += (
                ('requisition_id', '=', values['supplier'].purchase_requisition_id.id),
            )
        return domain


class StockMove(models.Model):
    _inherit = 'stock.move'

    requisition_line_ids = fields.One2many('purchase.requisition.line', 'move_dest_id')

    def _get_upstream_documents_and_responsibles(self, visited):
        # People without purchase rights should be able to do this operation
        requisition_lines_sudo = self.sudo().requisition_line_ids
        if requisition_lines_sudo:
            return [(requisition_line.requisition_id, requisition_line.requisition_id.user_id, visited) for requisition_line in requisition_lines_sudo if requisition_line.requisition_id.state not in ('done', 'cancel')]
        else:
            return super(StockMove, self)._get_upstream_documents_and_responsibles(visited)


class Orderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    def _quantity_in_progress(self):
        res = super(Orderpoint, self)._quantity_in_progress()
        for op in self:
            for pr in self.env['purchase.requisition'].search([('state', '=', 'draft'), ('origin', '=', op.name)]):
                for prline in pr.line_ids.filtered(lambda l: l.product_id.id == op.product_id.id and not l.move_dest_id):
                    res[op.id] += prline.product_uom_id._compute_quantity(prline.product_qty, op.product_uom, round=False)
        return res
