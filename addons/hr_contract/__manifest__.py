{
    'name': 'Employee Contracts',
    'version': '1.0',
    'category': 'Human Resources/Contracts',
    'sequence': 335,
    'description': """
Add all information on the employee form to manage contracts.
=============================================================

    * Contract
    * Place of Birth,
    * Medical Examination Date
    * Company Vehicle

You can assign several contracts per employee.
    """,
    'website': 'https://www.weth.com.br/page/employees',
    'depends': ['hr'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/hr_contract_data.xml',
        'views/hr_contract_views.xml',
        'views/assets.xml',
        'wizard/hr_departure_wizard_views.xml',
    ],
    'demo': ['data/hr_contract_demo.xml'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
