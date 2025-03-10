from odoo.tests.common import TransactionCase


class TestName(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product_name = 'Product Test Name'
        self.product_code = 'PTN'
        self.product = self.env['product.product'].create({
            'name': self.product_name,
            'default_code': self.product_code,
        })

    def test_10_product_name(self):
        display_name = self.product.display_name
        self.assertEqual(display_name, "[%s] %s" % (self.product_code, self.product_name),
                         "Code should be preprended the the name as the context is not preventing it.")
        display_name = self.product.with_context(display_default_code=False).display_name
        self.assertEqual(display_name, self.product_name,
                         "Code should not be preprended to the name as context should prevent it.")

    def test_default_code_and_negative_operator(self):
        res = self.env['product.template'].name_search(name='PTN', operator='not ilike')
        res_ids = [r[0] for r in res]
        self.assertNotIn(self.product.id, res_ids)
