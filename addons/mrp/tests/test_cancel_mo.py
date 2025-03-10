from odoo.tests import Form
from datetime import datetime, timedelta

from odoo.fields import Datetime as Dt
from odoo.exceptions import UserError
from odoo.addons.mrp.tests.common import TestMrpCommon


class TestMrpCancelMO(TestMrpCommon):

    def test_cancel_mo_without_routing_1(self):
        """ Cancel a Manufacturing Order with no routing, no production.
        """
        # Create MO
        manufacturing_order = self.generate_mo()[0]
        # Do nothing, cancel it
        manufacturing_order.action_cancel()
        # Check the MO and its moves are cancelled
        self.assertEqual(manufacturing_order.state, 'cancel', "MO should be in cancel state.")
        self.assertEqual(manufacturing_order.move_raw_ids[0].state, 'cancel',
            "Cancelled MO raw moves must be cancelled as well.")
        self.assertEqual(manufacturing_order.move_raw_ids[1].state, 'cancel',
            "Cancelled MO raw moves must be cancelled as well.")
        self.assertEqual(manufacturing_order.move_finished_ids.state, 'cancel',
            "Cancelled MO finished move must be cancelled as well.")

    def test_cancel_mo_without_routing_2(self):
        """ Cancel a Manufacturing Order with no routing but some productions.
        """
        # Create MO
        manufacturing_order = self.generate_mo()[0]
        # Produce some quantity
        mo_form = Form(manufacturing_order)
        mo_form.qty_producing = 2
        manufacturing_order = mo_form.save()
        # Cancel it
        manufacturing_order.action_cancel()
        # Check it's cancelled
        self.assertEqual(manufacturing_order.state, 'cancel', "MO should be in cancel state.")
        self.assertEqual(manufacturing_order.move_raw_ids[0].state, 'cancel',
            "Cancelled MO raw moves must be cancelled as well.")
        self.assertEqual(manufacturing_order.move_raw_ids[1].state, 'cancel',
            "Cancelled MO raw moves must be cancelled as well.")
        self.assertEqual(manufacturing_order.move_finished_ids.state, 'cancel',
            "Cancelled MO finished move must be cancelled as well.")

    def test_cancel_mo_without_routing_3(self):
        """ Cancel a Manufacturing Order with no routing but some productions
        after post inventory.
        """
        # Create MO
        manufacturing_order = self.generate_mo(consumption='strict')[0]
        # Produce some quantity (not all to avoid to done the MO when post inventory)
        mo_form = Form(manufacturing_order)
        mo_form.qty_producing = 2
        manufacturing_order = mo_form.save()
        # Post Inventory
        manufacturing_order._post_inventory()
        # Cancel the MO
        manufacturing_order.action_cancel()
        # Check MO is marked as done and its SML are done or cancelled
        self.assertEqual(manufacturing_order.state, 'done', "MO should be in done state.")
        self.assertEqual(manufacturing_order.move_raw_ids[0].state, 'done',
            "Due to 'post_inventory', some move raw must stay in done state")
        self.assertEqual(manufacturing_order.move_raw_ids[1].state, 'done',
            "Due to 'post_inventory', some move raw must stay in done state")
        self.assertEqual(manufacturing_order.move_raw_ids[2].state, 'cancel',
            "The other move raw are cancelled like their MO.")
        self.assertEqual(manufacturing_order.move_raw_ids[3].state, 'cancel',
            "The other move raw are cancelled like their MO.")
        self.assertEqual(manufacturing_order.move_finished_ids[0].state, 'done',
            "Due to 'post_inventory', a move finished must stay in done state")
        self.assertEqual(manufacturing_order.move_finished_ids[1].state, 'cancel',
            "The other move finished is cancelled like its MO.")

    def test_unlink_mo(self):
        """ Try to unlink a Manufacturing Order, and check it's possible or not
        depending of the MO state (must be in cancel state to be unlinked, but
        the unlink method will try to cancel MO before unlink them).
        """
        # Case #1: Create MO, do nothing and try to unlink it (can be deleted)
        manufacturing_order = self.generate_mo()[0]
        self.assertEqual(manufacturing_order.exists().state, 'confirmed')
        manufacturing_order.unlink()
        # Check the MO is deleted.
        self.assertEqual(manufacturing_order.exists().state, False)

        # Case #2: Create MO, make and post some production, then try to unlink
        # it (cannot be deleted)
        manufacturing_order = self.generate_mo()[0]
        # Produce some quantity (not all to avoid to done the MO when post inventory)
        mo_form = Form(manufacturing_order)
        mo_form.qty_producing = 2
        manufacturing_order = mo_form.save()
        # Post Inventory
        manufacturing_order._post_inventory()
        # Unlink the MO must raises an UserError since it cannot be really cancelled
        self.assertEqual(manufacturing_order.exists().state, 'progress')
        with self.assertRaises(UserError):
            manufacturing_order.unlink()

    def test_cancel_mo_with_workorder(self):
        """
            Create a manufacturing order without component and with a work order
            and check that when you cancel the MO, the WO is also canceled.
        """

        bom = self.env['mrp.bom'].create({
            'product_id': self.product_2.id,
            'product_tmpl_id': self.product_2.product_tmpl_id.id,
            'product_uom_id': self.product_2.uom_id.id,
            'consumption': 'flexible',
            'product_qty': 1.0,
            'operation_ids': [
                (0, 0, {'name': 'test_wo', 'workcenter_id': self.workcenter_1.id, 'time_cycle': 15, 'sequence': 1}),
            ],
            'type': 'normal',
            'sequence': 2,
            'bom_line_ids': []
            })

        # Create MO
        production_form = Form(self.env['mrp.production'])
        production_form.product_id = self.product_2
        production_form.bom_id = bom
        manufacturing_order = production_form.save()

        # Check that there is no component
        self.assertFalse(manufacturing_order.move_raw_ids.id)

        # Cancel the MO
        manufacturing_order.action_cancel()

        # Check that MO and WO are canceled
        self.assertEqual(manufacturing_order.state, 'cancel', "MO should be in cancel state.")
        self.assertEqual(manufacturing_order.workorder_ids.state, 'cancel', 'MO work orders must be cancelled as well.')
