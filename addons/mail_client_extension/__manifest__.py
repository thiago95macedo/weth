{
    'name': 'Mail Client Extension',
    'version': '1.0',
    'category': 'Sales/CRM',
    'sequence': 5,
    'summary': 'Turn emails received in your Outlook mailbox into leads and log their content as internal notes.',
    'description': "Turn emails received in your Outlook mailbox into leads and log their content as internal notes.",
    'website': 'https://www.weth.com.br/page/crm',
    'depends': [
        'web',
        'crm',
        'crm_iap_lead_enrich'
    ],
    'data': [
        'views/mail_client_extension_login.xml',
        'views/mail_client_extension_lead.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
