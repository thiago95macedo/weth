from odoo.tests import common


class TestStockLocationSearch(common.TransactionCase):
    def setUp(self):
        super(TestStockLocationSearch, self).setUp()
        self.location = self.env['stock.location']
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.sublocation = self.env['stock.location'].create({
            'name': 'Shelf 2',
            'barcode': 1201985,
            'location_id': self.stock_location.id
        })
        self.location_barcode_id = self.sublocation.id
        self.barcode = self.sublocation.barcode
        self.name = self.sublocation.name

    def test_10_location_search_by_barcode(self):
        """Search stock location by barcode"""
        location_names = self.location.name_search(name=self.barcode)
        self.assertEqual(len(location_names), 1)
        location_id_found = location_names[0][0]
        self.assertEqual(self.location_barcode_id, location_id_found)

    def test_20_location_search_by_name(self):
        """Search stock location by name"""
        location_names = self.location.name_search(name=self.name)
        location_ids_found = [location_name[0] for location_name in location_names]
        self.assertTrue(self.location_barcode_id in location_ids_found)

    def test_30_location_search_wo_results(self):
        """Search stock location without results"""
        location_names = self.location.name_search(name='nonexistent')
        self.assertFalse(location_names)
