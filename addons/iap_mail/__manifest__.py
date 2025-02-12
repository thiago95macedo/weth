
{
    'name': "IAP / Mail",
    'summary': """Bridge between IAP and mail""",
    'description': """Bridge between IAP and mail""",
    'category': 'Hidden/Tools',
    'version': '1.0',
    'depends': [
        'iap',
        'mail',
    ],
    'application': False,
    'installable': True,
    'auto_install': True,
    'data': [
        'views/mail_templates.xml',
    ],
    'license': 'LGPL-3',
}
