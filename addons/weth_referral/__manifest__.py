{
    'name': "WETH referral program",
    'summary': """Allow you to refer your friends to WETH and get rewards""",
    'category': 'Hidden',
    'version': '1.0',
    'depends': ['base', 'web'],
    'data': [
        'views/templates.xml',
    ],
    'qweb': [
        "static/src/xml/systray.xml",
    ],
    'auto_install': False,
    'license': 'LGPL-3',
}
