from odoo import SUPERUSER_ID
from odoo.http import Controller, request, route

class TestAssetsBundleController(Controller):
    @route('/test_assetsbundle/js', type='http', auth='user')
    def bundle(self):
        env = request.env(user=SUPERUSER_ID)
        bundle = env.ref('test_assetsbundle.bundle1')
        views = env['ir.ui.view'].search([('inherit_id', '=', bundle.id)])
        return views.with_context(check_view_ids=views.ids)._render_template('test_assetsbundle.template1')
