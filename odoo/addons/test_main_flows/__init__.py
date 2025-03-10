from odoo import api, SUPERUSER_ID

#
# Conditional installation of enterprise modules.
#
# This module is defined in community but some steps (defined with 'edition: "enterprise"')
# are only used to test enterprise. As it's not possible to direcly add enterprise
# modules dependencies, this post install hook will install account_accountant if exists.
#
def _auto_install_enterprise_dependencies(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    module_list = ['account_accountant']
    module_ids = env['ir.module.module'].search([('name', 'in', module_list), ('state', '=', 'uninstalled')])
    module_ids.sudo().button_install()
