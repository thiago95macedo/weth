{
    'name': 'IBAN Bank Accounts',
    'category': 'Hidden/Tools',
    'description': """
This module installs the base for IBAN (International Bank Account Number) bank accounts and checks for it's validity.
======================================================================================================================

The ability to extract the correctly represented local accounts from IBAN accounts
with a single statement.
    """,
    'depends': ['account', 'web'],
    'data': [
        'views/templates.xml',
        'views/partner_view.xml',
        'views/setup_wizards_view.xml'
    ],
    'demo': ['data/res_partner_bank_demo.xml'],
    'license': 'LGPL-3',
}
