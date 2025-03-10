from odoo.tests.common import HttpCase, tagged
from odoo.tools import mute_logger, logging
from unittest.mock import patch

@tagged('-at_install', 'post_install')
class TestHttpCase(HttpCase):

    def test_console_error_string(self):
        with self.assertRaises(AssertionError) as error_catcher:
            code = "console.error('test error','message')"
            with patch('odoo.tests.common.ChromeBrowser.take_screenshot', return_value=None):
                self.browser_js(url_path='about:blank', code=code)
        # second line must contains error message
        self.assertEqual(error_catcher.exception.args[0].splitlines()[1], "test error message")

    def test_console_error_object(self):
        with self.assertRaises(AssertionError) as error_catcher:
            code = "console.error(TypeError('test error message'))"
            with patch('odoo.tests.common.ChromeBrowser.take_screenshot', return_value=None):
                self.browser_js(url_path='about:blank', code=code)
        # second line must contains error message
        self.assertEqual(error_catcher.exception.args[0].splitlines()[1:3],
        ['TypeError: test error message', '    at <anonymous>:1:15'])

    def test_console_log_object(self):
        logger = logging.getLogger('odoo')
        level = logger.level
        logger.setLevel(logging.INFO)
        self.addCleanup(logger.setLevel, level)

        with self.assertLogs() as log_catcher:
            code = "console.log({custom:{1:'test', 2:'a'}, value:1, description:'dummy'});console.log('test successful');"
            self.browser_js(url_path='about:blank', code=code)
        console_log_count = 0
        for log in log_catcher.output:
            if '.browser:' in log:
                text = log.split('.browser:', 1)[1]
                if text == 'test successful':
                    continue
                self.assertEqual(text, "Object(custom=Object, value=1, description='dummy')")
                console_log_count +=1
        self.assertEqual(console_log_count, 1)
