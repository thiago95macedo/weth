from odoo.tests.common import SavepointCase, users


class TestSaleProject(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.analytic_account_sale = cls.env['account.analytic.account'].create({
            'name': 'Project for selling timesheet - AA',
            'code': 'AA-2030'
        })

        # Create projects
        cls.project_global = cls.env['project.project'].create({
            'name': 'Global Project',
            'analytic_account_id': cls.analytic_account_sale.id,
        })
        cls.project_template = cls.env['project.project'].create({
            'name': 'Project TEMPLATE for services',
        })
        cls.project_template_state = cls.env['project.task.type'].create({
            'name': 'Only stage in project template',
            'sequence': 1,
            'project_ids': [(4, cls.project_template.id)]
        })

        # Create service products
        uom_hour = cls.env.ref('uom.product_uom_hour')

        cls.product_order_service1 = cls.env['product.product'].create({
            'name': "Service Ordered, create no task",
            'standard_price': 11,
            'list_price': 13,
            'type': 'service',
            'invoice_policy': 'order',
            'uom_id': uom_hour.id,
            'uom_po_id': uom_hour.id,
            'default_code': 'SERV-ORDERED1',
            'service_tracking': 'no',
            'project_id': False,
        })
        cls.product_order_service2 = cls.env['product.product'].create({
            'name': "Service Ordered, create task in global project",
            'standard_price': 30,
            'list_price': 90,
            'type': 'service',
            'invoice_policy': 'order',
            'uom_id': uom_hour.id,
            'uom_po_id': uom_hour.id,
            'default_code': 'SERV-ORDERED2',
            'service_tracking': 'task_global_project',
            'project_id': cls.project_global.id,
        })
        cls.product_order_service3 = cls.env['product.product'].create({
            'name': "Service Ordered, create task in new project",
            'standard_price': 10,
            'list_price': 20,
            'type': 'service',
            'invoice_policy': 'order',
            'uom_id': uom_hour.id,
            'uom_po_id': uom_hour.id,
            'default_code': 'SERV-ORDERED3',
            'service_tracking': 'task_in_project',
            'project_id': False,  # will create a project
        })
        cls.product_order_service4 = cls.env['product.product'].create({
            'name': "Service Ordered, create project only",
            'standard_price': 15,
            'list_price': 30,
            'type': 'service',
            'invoice_policy': 'order',
            'uom_id': uom_hour.id,
            'uom_po_id': uom_hour.id,
            'default_code': 'SERV-ORDERED4',
            'service_tracking': 'project_only',
            'project_id': False,
        })
        cls.partner = cls.env['res.partner'].create({'name': "Mur en béton"})

    def test_sale_order_with_project_task(self):
        SaleOrderLine = self.env['sale.order.line'].with_context(tracking_disable=True)

        sale_order = self.env['sale.order'].with_context(tracking_disable=True).create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
        })
        so_line_order_no_task = SaleOrderLine.create({
            'name': self.product_order_service1.name,
            'product_id': self.product_order_service1.id,
            'product_uom_qty': 10,
            'product_uom': self.product_order_service1.uom_id.id,
            'price_unit': self.product_order_service1.list_price,
            'order_id': sale_order.id,
        })

        so_line_order_task_in_global = SaleOrderLine.create({
            'name': self.product_order_service2.name,
            'product_id': self.product_order_service2.id,
            'product_uom_qty': 10,
            'product_uom': self.product_order_service2.uom_id.id,
            'price_unit': self.product_order_service2.list_price,
            'order_id': sale_order.id,
        })

        so_line_order_new_task_new_project = SaleOrderLine.create({
            'name': self.product_order_service3.name,
            'product_id': self.product_order_service3.id,
            'product_uom_qty': 10,
            'product_uom': self.product_order_service3.uom_id.id,
            'price_unit': self.product_order_service3.list_price,
            'order_id': sale_order.id,
        })

        so_line_order_only_project = SaleOrderLine.create({
            'name': self.product_order_service4.name,
            'product_id': self.product_order_service4.id,
            'product_uom_qty': 10,
            'product_uom': self.product_order_service4.uom_id.id,
            'price_unit': self.product_order_service4.list_price,
            'order_id': sale_order.id,
        })
        sale_order.action_confirm()

        # service_tracking 'no'
        self.assertFalse(so_line_order_no_task.project_id, "The project should not be linked to no task product")
        self.assertFalse(so_line_order_no_task.task_id, "The task should not be linked to no task product")
        # service_tracking 'task_global_project'
        self.assertFalse(so_line_order_task_in_global.project_id, "Only task should be created, project should not be linked")
        self.assertEqual(self.project_global.tasks.sale_line_id, so_line_order_task_in_global, "Global project's task should be linked to so line")
        #  service_tracking 'task_in_project'
        self.assertTrue(so_line_order_new_task_new_project.project_id, "Sales order line should be linked to newly created project")
        self.assertTrue(so_line_order_new_task_new_project.task_id, "Sales order line should be linked to newly created task")
        # service_tracking 'project_only'
        self.assertFalse(so_line_order_only_project.task_id, "Task should not be created")
        self.assertTrue(so_line_order_only_project.project_id, "Sales order line should be linked to newly created project")

    def test_sol_product_type_update(self):
        sale_order = self.env['sale.order'].with_context(tracking_disable=True).create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
        })
        self.product_order_service3.type = 'consu'
        sale_order_line = self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'name': self.product_order_service3.name,
            'product_id': self.product_order_service3.id,
            'product_uom_qty': 5,
            'product_uom': self.product_order_service3.uom_id.id,
            'price_unit': self.product_order_service3.list_price
        })
        self.assertFalse(sale_order_line.is_service, "As the product is consumable, the SOL should not be a service")

        self.product_order_service3.type = 'service'
        self.assertTrue(sale_order_line.is_service, "As the product is a service, the SOL should be a service")

    @users('demo')
    def test_cancel_so_linked_to_project(self):
        """ Test that cancelling a SO linked to a project will not raise an error """
        # Ensure user don't have edit right access to the project
        group_sale_manager = self.env.ref('sales_team.group_sale_manager')
        group_project_user = self.env.ref('project.group_project_user')
        self.env.user.write({'groups_id': [(6, 0, [group_sale_manager.id, group_project_user.id])]})

        sale_order = self.env['sale.order'].with_context(tracking_disable=True).create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'project_id': self.project_global.id,
        })
        sale_order_line = self.env['sale.order.line'].create({
            'name': self.product_order_service2.name,
            'product_id': self.product_order_service2.id,
            'order_id': sale_order.id,
        })
        self.assertFalse(self.project_global.tasks.sale_line_id, "The project tasks should not be linked to the SOL")

        sale_order.action_confirm()
        self.assertEqual(self.project_global.tasks.sale_line_id.id, sale_order_line.id, "The project tasks should be linked to the SOL from the SO")

        self.project_global.sale_line_id = sale_order_line
        sale_order.action_cancel()
        self.assertFalse(self.project_global.sale_line_id, "The project should not be linked to the SOL anymore")
