from odoo import api, models, _

import logging
_logger = logging.getLogger(__name__)


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    @api.model
    def generate_journals(self, acc_template_ref, company, journals_dict=None):
        journal_to_add = [{'name': _('Inventory Valuation'), 'type': 'general', 'code': 'STJ', 'favorite': False, 'sequence': 8}]
        return super(AccountChartTemplate, self).generate_journals(acc_template_ref=acc_template_ref, company=company, journals_dict=journal_to_add)

    def generate_properties(self, acc_template_ref, company, property_list=None):
        res = super(AccountChartTemplate, self).generate_properties(acc_template_ref=acc_template_ref, company=company)
        PropertyObj = self.env['ir.property']  # Property Stock Journal
        value = self.env['account.journal'].search([('company_id', '=', company.id), ('code', '=', 'STJ'), ('type', '=', 'general')], limit=1)
        if value:
            PropertyObj._set_default("property_stock_journal", "product.category", value, company)

        todo_list = [  # Property Stock Accounts
            'property_stock_account_input_categ_id',
            'property_stock_account_output_categ_id',
            'property_stock_valuation_account_id',
        ]
        categ_values = {category.id: False for category in self.env['product.category'].search([])}
        for field in todo_list:
            account = self[field]
            value = acc_template_ref[account.id] if account else False
            PropertyObj._set_default(field, "product.category", value, company)
            PropertyObj._set_multi(field, "product.category", categ_values, True)

        return res
