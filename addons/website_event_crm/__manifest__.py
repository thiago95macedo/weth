{
    'name': 'Website Events CRM',
    'version': '1.0',
    'category': 'Website/Website',
    'website': 'https://www.weth.com.br/page/events',
    'description': "Allow per-order lead creation mode",
    'depends': ['event_crm', 'website_event'],
    'data': [
        'views/event_lead_rule_views.xml',
    ],
    'demo': [
        'data/event_crm_demo.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
