from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase


class TestIrCron(TransactionCase):

    def setUp(self):
        super(TestIrCron, self).setUp()

        self.cron = self.env['ir.cron'].create({
            'name': 'TestCron',
            'model_id': self.env.ref('base.model_res_partner').id,
            'state': 'code',
            'code': 'model.search([("name", "=", "TestCronRecord")]).write({"name": "You have been CRONWNED"})',
            'interval_number': 1,
            'interval_type': 'days',
            'numbercall': -1,
            'doall': False,
        })
        self.test_partner = self.env['res.partner'].create({
            'name': 'TestCronRecord'
        })
        self.test_partner2 = self.env['res.partner'].create({
            'name': 'NotTestCronRecord'
        })

    def test_cron_direct_trigger(self):
        self.assertFalse(self.cron.lastcall)
        self.assertEqual(self.test_partner.name, 'TestCronRecord')
        self.assertEqual(self.test_partner2.name, 'NotTestCronRecord')

        def patched_now(*args, **kwargs):
            return '2020-10-22 08:00:00'

        with patch('odoo.fields.Datetime.now', patched_now):
            self.cron.method_direct_trigger()

        self.assertEqual(fields.Datetime.to_string(self.cron.lastcall), '2020-10-22 08:00:00')
        self.assertEqual(self.test_partner.name, 'You have been CRONWNED')
        self.assertEqual(self.test_partner2.name, 'NotTestCronRecord')
