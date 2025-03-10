import odoo.tests
from odoo.addons.product_matrix.tests import common


@odoo.tests.tagged('post_install', '-at_install')
class TestSaleMatrixUi(common.TestMatrixCommon):

    """
        This test needs sale_management module to work.
    """

    def test_sale_matrix_ui(self):
        # Set the template as configurable by matrix.
        self.matrix_template.product_add_mode = "matrix"

        self.start_tour("/web", 'sale_matrix_tour', login="admin")

        # Ensures some dynamic create variants have been created by the matrix
        # Ensures a SO has been created with exactly x lines ...

        self.assertEqual(len(self.matrix_template.product_variant_ids), 8)
        self.assertEqual(len(self.matrix_template.product_variant_ids.product_template_attribute_value_ids), 6)
        self.assertEqual(len(self.matrix_template.attribute_line_ids.product_template_value_ids), 8)
        self.env['sale.order.line'].search([('product_id', 'in', self.matrix_template.product_variant_ids.ids)]).order_id.action_confirm()

        self.matrix_template.flush()
        self.assertEqual(round(self.matrix_template.sales_count, 2), 56.8)
        for variant in self.matrix_template.product_variant_ids:
            # 5 and 9.2 because of no variant attributes
            self.assertIn(round(variant.sales_count, 2), [5, 9.2])

        # Ensure no duplicate line has been created on the SO.
        # NB: the *2 is because the no_variant attribute doesn't create a variant
        # but still gives different order lines.
        self.assertEqual(
            len(self.env['sale.order.line'].search([('product_id', 'in', self.matrix_template.product_variant_ids.ids)])),
            len(self.matrix_template.product_variant_ids)*2
        )
