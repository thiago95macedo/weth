{
    'name': "pos_hr",
    'category': "Hidden",
    'summary': 'Link module between Point of Sale and HR',

    'description': """
This module allows Employees (and not users) to log in to the Point of Sale application using a barcode, a PIN number or both.
The actual till still requires one user but an unlimited number of employees can log on to that till and process sales.
    """,

    'depends': ['point_of_sale', 'hr'],

    'data': [
        'views/pos_config.xml',
        'views/point_of_sale.xml',
        'views/pos_order_view.xml',
        'views/pos_order_report_view.xml',
    ],
    'installable': True,
    'auto_install': True,
    'qweb': [
        'static/src/xml/HeaderLockButton.xml',
        'static/src/xml/Chrome.xml',
        'static/src/xml/CashierName.xml',
        'static/src/xml/LoginScreen.xml',
    ],
    'license': 'LGPL-3',
}
