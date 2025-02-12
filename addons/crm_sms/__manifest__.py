{
    'name': 'SMS in CRM',
    'version': '1.0',
    'category': 'Sales/CRM',
    'summary': 'Add SMS capabilities to CRM',
    'description': "",
    'depends': ['crm', 'sms'],
    'data': [
        'views/crm_lead_views.xml',
        'security/ir.model.access.csv',
        'security/sms_security.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
    'license': 'LGPL-3',
}
