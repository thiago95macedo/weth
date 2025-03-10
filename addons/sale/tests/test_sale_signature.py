from odoo.addons.base.tests.common import HttpCaseWithUserPortal
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestSaleSignature(HttpCaseWithUserPortal):
    def test_01_portal_sale_signature_tour(self):
        """The goal of this test is to make sure the portal user can sign SO."""

        portal_user = self.partner_portal
        # create a SO to be signed
        sales_order = self.env['sale.order'].create({
            'name': 'test SO',
            'partner_id': portal_user.id,
            'state': 'sent',
            'require_payment': False,
        })
        self.env['sale.order.line'].create({
            'order_id': sales_order.id,
            'product_id': self.env['product.product'].create({'name': 'A product'}).id,
        })

        # must be sent to the user so he can see it
        email_act = sales_order.action_quotation_send()
        email_ctx = email_act.get('context', {})
        sales_order.with_context(**email_ctx).message_post_with_template(email_ctx.get('default_template_id'))

        self.start_tour("/", 'sale_signature', login="portal")
