import base64
import difflib
import io
import pprint
import unittest

from odoo.tests.common import TransactionCase, can_import
from odoo.modules.module import get_module_resource
from odoo.tools import mute_logger, pycompat

ID_FIELD = {
    'id': 'id',
    'name': 'id',
    'string': "External ID",

    'required': False,
    'fields': [],
    'type': 'id',
}


def make_field(name='value', string='Value', required=False, fields=[], field_type='id'):
    return [
        ID_FIELD,
        {'id': name, 'name': name, 'string': string, 'required': required, 'fields': fields, 'type': field_type},
    ]


def sorted_fields(fields):
    """ recursively sort field lists to ease comparison """
    recursed = [dict(field, fields=sorted_fields(field['fields'])) for field in fields]
    return sorted(recursed, key=lambda field: field['id'])


class BaseImportCase(TransactionCase):

    def assertEqualFields(self, fields1, fields2):
        f1 = sorted_fields(fields1)
        f2 = sorted_fields(fields2)
        assert f1 == f2, '\n'.join(difflib.unified_diff(
            pprint.pformat(f1).splitlines(),
            pprint.pformat(f2).splitlines()
        ))

class TestBasicFields(BaseImportCase):

    def get_fields(self, field):
        return self.env['base_import.import'].get_fields('base_import.tests.models.' + field)

    def test_base(self):
        """ A basic field is not required """
        self.assertEqualFields(self.get_fields('char'), make_field(field_type='char'))

    def test_required(self):
        """ Required fields should be flagged (so they can be fill-required) """
        self.assertEqualFields(self.get_fields('char.required'), make_field(required=True, field_type='char'))

    def test_readonly(self):
        """ Readonly fields should be filtered out"""
        self.assertEqualFields(self.get_fields('char.readonly'), [ID_FIELD])

    def test_readonly_states(self):
        """ Readonly fields with states should not be filtered out"""
        self.assertEqualFields(self.get_fields('char.states'), make_field(field_type='char'))

    def test_readonly_states_noreadonly(self):
        """ Readonly fields with states having nothing to do with
        readonly should still be filtered out"""
        self.assertEqualFields(self.get_fields('char.noreadonly'), [ID_FIELD])

    def test_readonly_states_stillreadonly(self):
        """ Readonly fields with readonly states leaving them readonly
        always... filtered out"""
        self.assertEqualFields(self.get_fields('char.stillreadonly'), [ID_FIELD])

    def test_m2o(self):
        """ M2O fields should allow import of themselves (name_get),
        their id and their xid"""
        self.assertEqualFields(self.get_fields('m2o'), make_field(field_type='many2one', fields=[
            {'id': 'value', 'name': 'id', 'string': 'External ID', 'required': False, 'fields': [], 'type': 'id'},
            {'id': 'value', 'name': '.id', 'string': 'Database ID', 'required': False, 'fields': [], 'type': 'id'},
        ]))

    def test_m2o_required(self):
        """ If an m2o field is required, its three sub-fields are
        required as well (the client has to handle that: requiredness
        is id-based)
        """
        self.assertEqualFields(self.get_fields('m2o.required'), make_field(field_type='many2one', required=True, fields=[
            {'id': 'value', 'name': 'id', 'string': 'External ID', 'required': True, 'fields': [], 'type': 'id'},
            {'id': 'value', 'name': '.id', 'string': 'Database ID', 'required': True, 'fields': [], 'type': 'id'},
        ]))


class TestO2M(BaseImportCase):

    def get_fields(self, field):
        return self.env['base_import.import'].get_fields('base_import.tests.models.' + field)

    def test_shallow(self):
        self.assertEqualFields(
            self.get_fields('o2m'), [
                ID_FIELD,
                {'id': 'name', 'name': 'name', 'string': "Name", 'required': False, 'fields': [], 'type': 'char',},
                {
                    'id': 'value', 'name': 'value', 'string': 'Value',
                    'required': False, 'type': 'one2many',
                    'fields': [
                        ID_FIELD,
                        {
                            'id': 'parent_id', 'name': 'parent_id',
                            'string': 'Parent', 'type': 'many2one',
                            'required': False, 'fields': [
                                {'id': 'parent_id', 'name': 'id',
                                 'string': 'External ID', 'required': False,
                                 'fields': [], 'type': 'id'},
                                {'id': 'parent_id', 'name': '.id',
                                 'string': 'Database ID', 'required': False,
                                 'fields': [], 'type': 'id'},
                            ]
                        },
                        {'id': 'value', 'name': 'value', 'string': 'Value',
                         'required': False, 'fields': [], 'type': 'integer'
                        },
                    ]
                }
            ]
        )


class TestMatchHeadersSingle(TransactionCase):

    def test_match_by_name(self):
        match = self.env['base_import.import']._match_header('f0', [{'name': 'f0'}], {})
        self.assertEqual(match, [{'name': 'f0'}])

    def test_match_by_string(self):
        match = self.env['base_import.import']._match_header('some field', [{'name': 'bob', 'string': "Some Field"}], {})
        self.assertEqual(match, [{'name': 'bob', 'string': "Some Field"}])

    def test_nomatch(self):
        match = self.env['base_import.import']._match_header('should not be', [{'name': 'bob', 'string': "wheee"}], {})
        self.assertEqual(match, [])

    def test_recursive_match(self):
        f = {
            'name': 'f0',
            'string': "My Field",
            'fields': [
                {'name': 'f0', 'string': "Sub field 0", 'fields': []},
                {'name': 'f1', 'string': "Sub field 2", 'fields': []},
            ]
        }
        match = self.env['base_import.import']._match_header('f0/f1', [f], {})
        self.assertEqual(match, [f, f['fields'][1]])

    def test_recursive_nomatch(self):
        """ Match first level, fail to match second level
        """
        f = {
            'name': 'f0',
            'string': "My Field",
            'fields': [
                {'name': 'f0', 'string': "Sub field 0", 'fields': []},
                {'name': 'f1', 'string': "Sub field 2", 'fields': []},
            ]
        }
        match = self.env['base_import.import']._match_header('f0/f2', [f], {})
        self.assertEqual(match, [])


class TestMatchHeadersMultiple(TransactionCase):

    def test_noheaders(self):
        self.assertEqual(
            self.env['base_import.import']._match_headers([], [], {}), ([], {})
        )

    def test_nomatch(self):
        self.assertEqual(
            self.env['base_import.import']._match_headers(
                iter([
                    ['foo', 'bar', 'baz', 'qux'],
                    ['v1', 'v2', 'v3', 'v4'],
                ]),
                [],
                {'headers': True}),
            (
                ['foo', 'bar', 'baz', 'qux'],
                dict.fromkeys(range(4))
            )
        )

    def test_mixed(self):
        self.assertEqual(
            self.env['base_import.import']._match_headers(
                iter(['foo bar baz qux/corge'.split()]),
                [
                    {'name': 'bar', 'string': 'Bar'},
                    {'name': 'bob', 'string': 'Baz'},
                    {'name': 'qux', 'string': 'Qux', 'fields': [
                        {'name': 'corge', 'fields': []},
                     ]}
                ],
                {'headers': True}),
            (['foo', 'bar', 'baz', 'qux/corge'], {
                0: None,
                1: ['bar'],
                2: ['bob'],
                3: ['qux', 'corge'],
            })
        )


class TestColumnMapping(TransactionCase):

    def test_column_mapping(self):
        import_record = self.env['base_import.import'].create({
            'res_model': 'base_import.tests.models.preview',
            'file': u"Name,Some Value,value\n"
                    u"chhagan,10,1\n"
                    u"magan,20,2\n".encode('utf-8'),
            'file_type': 'text/csv',
            'file_name': 'data.csv',
        })
        import_record.do(
            ['name', 'somevalue', 'othervalue'],
            ['Name', 'Some Value', 'value'],
            {'quoting': '"', 'separator': ',', 'headers': True},
            True
        )
        fields = self.env['base_import.mapping'].search_read(
            [('res_model', '=', 'base_import.tests.models.preview')],
            ['column_name', 'field_name']
        )
        self.assertItemsEqual([f['column_name'] for f in fields], ['Name', 'Some Value', 'value'])
        self.assertItemsEqual([f['field_name'] for f in fields], ['somevalue', 'name', 'othervalue'])


class TestPreview(TransactionCase):

    def make_import(self):
        import_wizard = self.env['base_import.import'].create({
            'res_model': 'res.users',
            'file': u"로그인,언어\nbob,1\n".encode('euc_kr'),
            'file_type': 'text/csv',
            'file_name': 'kr_data.csv',
        })
        return import_wizard

    @mute_logger('odoo.addons.base_import.models.base_import')
    def test_encoding(self):
        import_wizard = self.make_import()
        result = import_wizard.parse_preview({
            'quoting': '"',
            'separator': ',',
        })
        self.assertFalse('error' in result)

    @mute_logger('odoo.addons.base_import.models.base_import')
    def test_csv_errors(self):
        import_wizard = self.make_import()

        result = import_wizard.parse_preview({
            'quoting': 'foo',
            'separator': ',',
        })
        self.assertTrue('error' in result)

        result = import_wizard.parse_preview({
            'quoting': '"',
            'separator': 'bob',
        })
        self.assertTrue('error' in result)

    def test_csv_success(self):
        import_wizard = self.env['base_import.import'].create({
            'res_model': 'base_import.tests.models.preview',
            'file': b'name,Some Value,Counter\n'
                    b'foo,1,2\n'
                    b'bar,3,4\n'
                    b'qux,5,6\n',
            'file_type': 'text/csv'
        })

        result = import_wizard.parse_preview({
            'quoting': '"',
            'separator': ',',
            'headers': True,
        })
        self.assertIsNone(result.get('error'))
        self.assertEqual(result['matches'], {0: ['name'], 1: ['somevalue'], 2: None})
        self.assertEqual(result['headers'], ['name', 'Some Value', 'Counter'])
        # Order depends on iteration order of fields_get
        self.assertItemsEqual(result['fields'], [
            ID_FIELD,
            {'id': 'name', 'name': 'name', 'string': 'Name', 'required': False, 'fields': [], 'type': 'char'},
            {'id': 'somevalue', 'name': 'somevalue', 'string': 'Some Value', 'required': True, 'fields': [], 'type': 'integer'},
            {'id': 'othervalue', 'name': 'othervalue', 'string': 'Other Variable', 'required': False, 'fields': [], 'type': 'integer'},
        ])
        self.assertEqual(result['preview'], [
            ['foo', '1', '2'],
            ['bar', '3', '4'],
            ['qux', '5', '6'],
        ])

    @unittest.skipUnless(can_import('xlrd'), "XLRD module not available")
    def test_xls_success(self):
        xls_file_path = get_module_resource('base_import', 'tests', 'test.xls')
        file_content = open(xls_file_path, 'rb').read()
        import_wizard = self.env['base_import.import'].create({
            'res_model': 'base_import.tests.models.preview',
            'file': file_content,
            'file_type': 'application/vnd.ms-excel'
        })

        result = import_wizard.parse_preview({
            'headers': True,
        })
        self.assertIsNone(result.get('error'))
        self.assertEqual(result['matches'], {0: ['name'], 1: ['somevalue'], 2: None})
        self.assertEqual(result['headers'], ['name', 'Some Value', 'Counter'])
        self.assertItemsEqual(result['fields'], [
            ID_FIELD,
            {'id': 'name', 'name': 'name', 'string': 'Name', 'required': False, 'fields': [], 'type': 'char'},
            {'id': 'somevalue', 'name': 'somevalue', 'string': 'Some Value', 'required': True, 'fields': [], 'type': 'integer'},
            {'id': 'othervalue', 'name': 'othervalue', 'string': 'Other Variable', 'required': False, 'fields': [], 'type': 'integer'},
        ])
        self.assertEqual(result['preview'], [
            ['foo', '1', '2'],
            ['bar', '3', '4'],
            ['qux', '5', '6'],
        ])

    @unittest.skipUnless(can_import('xlrd.xlsx'), "XLRD/XLSX not available")
    def test_xlsx_success(self):
        xlsx_file_path = get_module_resource('base_import', 'tests', 'test.xlsx')
        file_content = open(xlsx_file_path, 'rb').read()
        import_wizard = self.env['base_import.import'].create({
            'res_model': 'base_import.tests.models.preview',
            'file': file_content,
            'file_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        result = import_wizard.parse_preview({
            'headers': True,
        })
        self.assertIsNone(result.get('error'))
        self.assertEqual(result['matches'], {0: ['name'], 1: ['somevalue'], 2: None})
        self.assertEqual(result['headers'], ['name', 'Some Value', 'Counter'])
        self.assertItemsEqual(result['fields'], [
            ID_FIELD,
            {'id': 'name', 'name': 'name', 'string': 'Name', 'required': False, 'fields': [], 'type': 'char'},
            {'id': 'somevalue', 'name': 'somevalue', 'string': 'Some Value', 'required': True, 'fields': [], 'type': 'integer'},
            {'id': 'othervalue', 'name': 'othervalue', 'string': 'Other Variable', 'required': False, 'fields': [], 'type': 'integer'},
        ])
        self.assertEqual(result['preview'], [
            ['foo', '1', '2'],
            ['bar', '3', '4'],
            ['qux', '5', '6'],
        ])

    @unittest.skipUnless(can_import('odf'), "ODFPY not available")
    def test_ods_success(self):
        ods_file_path = get_module_resource('base_import', 'tests', 'test.ods')
        file_content = open(ods_file_path, 'rb').read()
        import_wizard = self.env['base_import.import'].create({
            'res_model': 'base_import.tests.models.preview',
            'file': file_content,
            'file_type': 'application/vnd.oasis.opendocument.spreadsheet'
        })

        result = import_wizard.parse_preview({
            'headers': True,
        })
        self.assertIsNone(result.get('error'))
        self.assertEqual(result['matches'], {0: ['name'], 1: ['somevalue'], 2: None})
        self.assertEqual(result['headers'], ['name', 'Some Value', 'Counter'])
        self.assertItemsEqual(result['fields'], [
            ID_FIELD,
            {'id': 'name', 'name': 'name', 'string': 'Name', 'required': False, 'fields': [], 'type': 'char'},
            {'id': 'somevalue', 'name': 'somevalue', 'string': 'Some Value', 'required': True, 'fields': [], 'type': 'integer'},
            {'id': 'othervalue', 'name': 'othervalue', 'string': 'Other Variable', 'required': False, 'fields': [], 'type': 'integer'},
        ])
        self.assertEqual(result['preview'], [
            ['foo', '1', '2'],
            ['bar', '3', '4'],
            ['aux', '5', '6'],
        ])

class test_convert_import_data(TransactionCase):
    """ Tests conversion of base_import.import input into data which
    can be fed to Model.load
    """
    def test_all(self):
        import_wizard = self.env['base_import.import'].create({
            'res_model': 'base_import.tests.models.preview',
            'file': b'name,Some Value,Counter\n'
                    b'foo,1,2\n'
                    b'bar,3,4\n'
                    b'qux,5,6\n',
            'file_type': 'text/csv'

        })
        data, fields = import_wizard._convert_import_data(
            ['name', 'somevalue', 'othervalue'],
            {'quoting': '"', 'separator': ',', 'headers': True}
        )

        self.assertItemsEqual(fields, ['name', 'somevalue', 'othervalue'])
        self.assertItemsEqual(data, [
            ['foo', '1', '2'],
            ['bar', '3', '4'],
            ['qux', '5', '6'],
        ])

    def test_date_fields(self):
        import_wizard = self.env['base_import.import'].create({
            'res_model': 'res.partner',
            'file': u'name,date,create_date\n'
                    u'"foo","2013年07月18日","2016-10-12 06:06"\n'.encode('utf-8'),
            'file_type': 'text/csv'

        })

        results = import_wizard.do(
            ['name', 'date', 'create_date'],
            [],
            {
                'date_format': '%Y年%m月%d日',
                'datetime_format': '%Y-%m-%d %H:%M',
                'quoting': '"',
                'separator': ',',
                'headers': True
            }
        )

        # if results empty, no errors
        self.assertItemsEqual(results['messages'], [])

    def test_parse_relational_fields(self):
        """ Ensure that relational fields float and date are correctly
        parsed during the import call.
        """
        import_wizard = self.env['base_import.import'].create({
            'res_model': 'res.partner',
            'file': u'name,parent_id/id,parent_id/date,parent_id/credit_limit\n'
                    u'"foo","__export__.res_partner_1","2017年10月12日","5,69"\n'.encode('utf-8'),
            'file_type': 'text/csv'

        })
        options = {
            'date_format': '%Y年%m月%d日',
            'quoting': '"',
            'separator': ',',
            'float_decimal_separator': ',',
            'float_thousand_separator': '.',
            'headers': True
        }
        data, import_fields = import_wizard._convert_import_data(
            ['name', 'parent_id/.id', 'parent_id/date', 'parent_id/credit_limit'],
            options
        )
        result = import_wizard._parse_import_data(data, import_fields, options)
        # Check if the data 5,69 as been correctly parsed.
        self.assertEqual(float(result[0][-1]), 5.69)
        self.assertEqual(str(result[0][-2]), '2017-10-12')

    def test_parse_scientific_notation(self):
        """ Ensure that scientific notation is correctly converted to decimal """
        import_wizard = self.env['base_import.import']

        test_options = {}
        test_data = [
            ["1E+05"],
            ["1.20E-05"],
            ["1,9e5"],
            ["9,5e-5"],
        ]
        expected_result = [
            ["100000.000000"],
            ["0.000012"],
            ["190000.000000"],
            ["0.000095"],
        ]

        import_wizard._parse_float_from_data(test_data, 0, 'test-name', test_options)
        self.assertEqual(test_data, expected_result)

    def test_filtered(self):
        """ If ``False`` is provided as field mapping for a column,
        that column should be removed from importable data
        """
        import_wizard = self.env['base_import.import'].create({
            'res_model': 'base_import.tests.models.preview',
            'file': b'name,Some Value,Counter\n'
                    b'foo,1,2\n'
                    b'bar,3,4\n'
                    b'qux,5,6\n',
            'file_type': 'text/csv'
        })
        data, fields = import_wizard._convert_import_data(
            ['name', False, 'othervalue'],
            {'quoting': '"', 'separator': ',', 'headers': True}
        )

        self.assertItemsEqual(fields, ['name', 'othervalue'])
        self.assertItemsEqual(data, [
            ['foo', '2'],
            ['bar', '4'],
            ['qux', '6'],
        ])

    def test_norow(self):
        """ If a row is composed only of empty values (due to having
        filtered out non-empty values from it), it should be removed
        """
        import_wizard = self.env['base_import.import'].create({
            'res_model': 'base_import.tests.models.preview',
            'file': b'name,Some Value,Counter\n'
                    b'foo,1,2\n'
                    b',3,\n'
                    b',5,6\n',
            'file_type': 'text/csv'
        })
        data, fields = import_wizard._convert_import_data(
            ['name', False, 'othervalue'],
            {'quoting': '"', 'separator': ',', 'headers': True}
        )

        self.assertItemsEqual(fields, ['name', 'othervalue'])
        self.assertItemsEqual(data, [
            ['foo', '2'],
            ['', '6'],
        ])

    def test_empty_rows(self):
        import_wizard = self.env['base_import.import'].create({
            'res_model': 'base_import.tests.models.preview',
            'file': b'name,Some Value\n'
                    b'foo,1\n'
                    b'\n'
                    b'bar,2\n'
                    b'     \n'
                    b'\t \n',
            'file_type': 'text/csv'
        })
        data, fields = import_wizard._convert_import_data(
            ['name', 'somevalue'],
            {'quoting': '"', 'separator': ',', 'headers': True}
        )

        self.assertItemsEqual(fields, ['name', 'somevalue'])
        self.assertItemsEqual(data, [
            ['foo', '1'],
            ['bar', '2'],
        ])

    def test_nofield(self):
        import_wizard = self.env['base_import.import'].create({
            'res_model': 'base_import.tests.models.preview',
            'file': b'name,Some Value,Counter\n'
                    b'foo,1,2\n',
            'file_type': 'text/csv'

        })
        self.assertRaises(ValueError, import_wizard._convert_import_data, [], {'quoting': '"', 'separator': ',', 'headers': True})

    def test_falsefields(self):
        import_wizard = self.env['base_import.import'].create({
            'res_model': 'base_import.tests.models.preview',
            'file': b'name,Some Value,Counter\n'
                    b'foo,1,2\n',
            'file_type': 'text/csv'
        })

        self.assertRaises(
            ValueError,
            import_wizard._convert_import_data,
            [False, False, False],
            {'quoting': '"', 'separator': ',', 'headers': True})

    def test_newline_import(self):
        """
        Ensure importing keep newlines
        """
        output = io.BytesIO()
        writer = pycompat.csv_writer(output, quoting=1)

        data_row = [u"\tfoo\n\tbar", u" \"hello\" \n\n 'world' "]

        writer.writerow([u"name", u"Some Value"])
        writer.writerow(data_row)

        import_wizard = self.env['base_import.import'].create({
            'res_model': 'base_import.tests.models.preview',
            'file': output.getvalue(),
            'file_type': 'text/csv',
        })
        data, _ = import_wizard._convert_import_data(
            ['name', 'somevalue'],
            {'quoting': '"', 'separator': ',', 'headers': True}
        )

        self.assertItemsEqual(data, [data_row])

class TestBatching(TransactionCase):
    def _makefile(self, rows):
        f = io.BytesIO()
        writer = pycompat.csv_writer(f, quoting=1)
        writer.writerow(['name', 'counter'])
        for i in range(rows):
            writer.writerow(['n_%d' % i, str(i)])
        return f.getvalue()

    def test_recognize_batched(self):
        import_wizard = self.env['base_import.import'].create({
            'res_model': 'base_import.tests.models.preview',
            'file_type': 'text/csv',
        })

        import_wizard.file = self._makefile(10)
        result = import_wizard.parse_preview({
            'quoting': '"',
            'separator': ',',
            'headers': True,
            'limit': 100,
        })
        self.assertIsNone(result.get('error'))
        self.assertIs(result['batch'], False)

        result = import_wizard.parse_preview({
            'quoting': '"',
            'separator': ',',
            'headers': True,
            'limit': 5,
        })
        self.assertIsNone(result.get('error'))
        self.assertIs(result['batch'], True)

    def test_limit_on_lines(self):
        """ The limit option should be a limit on the number of *lines*
        imported at at time, not the number of *records*. This is relevant
        when it comes to embedded o2m.

        A big question is whether we want to round up or down (if the limit
        brings us inside a record). Rounding up (aka finishing up the record
        we're currently parsing) seems like a better idea:

        * if the first record has so many sub-lines it hits the limit we still
          want to import it (it's probably extremely rare but it can happen)
        * if we have one line per record, we probably want to import <limit>
          records not <limit-1>, but if we stop in the middle of the "current
          record" we'd always ignore the last record (I think)
        """
        f = io.BytesIO()
        writer = pycompat.csv_writer(f, quoting=1)
        writer.writerow(['name', 'value/value'])
        for record in range(10):
            writer.writerow(['record_%d' % record, '0'])
            for row in range(1, 10):
                writer.writerow(['', str(row)])

        import_wizard = self.env['base_import.import'].create({
            'res_model': 'base_import.tests.models.o2m',
            'file_type': 'text/csv',
            'file_name': 'things.csv',
            'file': f.getvalue(),
        })
        opts = {'quoting': '"', 'separator': ',', 'headers': True}
        preview = import_wizard.parse_preview({**opts, 'limit': 15})
        self.assertIs(preview['batch'], True)

        results = import_wizard.do(
            ['name', 'value/value'], [],
            {**opts, 'limit': 5}
        )
        self.assertFalse(results['messages'])
        self.assertEqual(len(results['ids']), 1, "should have imported the first record in full, got %s" % results['ids'])
        self.assertEqual(results['nextrow'], 10)

        results = import_wizard.do(
            ['name', 'value/value'], [],
            {**opts, 'limit': 15}
        )
        self.assertFalse(results['messages'])
        self.assertEqual(len(results['ids']), 2, "should have importe the first two records, got %s" % results['ids'])
        self.assertEqual(results['nextrow'], 20)


    def test_batches(self):
        partners_before = self.env['res.partner'].search([])
        opts = {'headers': True, 'separator': ',', 'quoting': '"'}

        import_wizard = self.env['base_import.import'].create({
            'res_model': 'res.partner',
            'file_type': 'text/csv',
            'file_name': 'clients.csv',
            'file': b"""name,email
a,a@example.com
b,b@example.com
,
c,c@example.com
d,d@example.com
e,e@example.com
f,f@example.com
g,g@example.com
"""
        })

        results = import_wizard.do(['name', 'email'], [], {**opts, 'limit': 1})
        self.assertFalse(results['messages'])
        self.assertEqual(len(results['ids']), 1)
        # titlerow is ignored by lastrow's counter
        self.assertEqual(results['nextrow'], 1)
        partners_1 = self.env['res.partner'].search([]) - partners_before
        self.assertEqual(partners_1.name, 'a')

        results = import_wizard.do(['name', 'email'], [], {**opts, 'limit': 2, 'skip': 1})
        self.assertFalse(results['messages'])
        self.assertEqual(len(results['ids']), 2)
        # empty row should also be ignored
        self.assertEqual(results['nextrow'], 3)
        partners_2 = self.env['res.partner'].search([]) - (partners_before | partners_1)
        self.assertEqual(partners_2.mapped('name'), ['b', 'c'])

        results = import_wizard.do(['name', 'email'], [], {**opts, 'limit': 10, 'skip': 3})
        self.assertFalse(results['messages'])
        self.assertEqual(len(results['ids']), 4)
        self.assertEqual(results['nextrow'], 0)
        partners_3 = self.env['res.partner'].search([]) - (partners_before | partners_1 | partners_2)
        self.assertEqual(partners_3.mapped('name'), ['d', 'e', 'f', 'g'])

class test_failures(TransactionCase):
    def test_big_attachments(self):
        """
        Ensure big fields (e.g. b64-encoded image data) can be imported and
        we're not hitting limits of the default CSV parser config
        """
        from PIL import Image

        im = Image.new('RGB', (1920, 1080))
        fout = io.BytesIO()

        writer = pycompat.csv_writer(fout, dialect=None)
        writer.writerows([
            [u'name', u'db_datas'],
            [u'foo', base64.b64encode(im.tobytes()).decode('ascii')]
        ])

        import_wizard = self.env['base_import.import'].create({
            'res_model': 'ir.attachment',
            'file': fout.getvalue(),
            'file_type': 'text/csv'
        })
        results = import_wizard.do(
            ['name', 'db_datas'],
            [],
            {'headers': True, 'separator': ',', 'quoting': '"'})
        self.assertFalse(results['messages'], "results should be empty on successful import")
