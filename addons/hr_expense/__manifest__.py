
{
    'name': 'Expenses',
    'version': '2.0',
    'category': 'Human Resources/Expenses',
    'sequence': 70,
    'summary': 'Submit, validate and reinvoice employee expenses',
    'description': """
Manage expenses by Employees
============================

This application allows you to manage your employees' daily expenses. It gives you access to your employees’ fee notes and give you the right to complete and validate or refuse the notes. After validation it creates an invoice for the employee.
Employee can encode their own expenses and the validation flow puts it automatically in the accounting after validation by managers.


The whole flow is implemented as:
---------------------------------
* Draft expense
* Submitted by the employee to his manager
* Approved by his manager
* Validation by the accountant and accounting entries creation

This module also uses analytic accounting and is compatible with the invoice on timesheet module so that you are able to automatically re-invoice your customers' expenses if your work by project.
    """,
    'website': 'https://www.weth.com.br/page/expenses',
    'depends': ['hr_contract', 'account', 'web_tour'],
    'data': [
        'security/hr_expense_security.xml',
        'security/ir.model.access.csv',
        'data/digest_data.xml',
        'data/mail_data.xml',
        'data/hr_expense_sequence.xml',
        'data/hr_expense_data.xml',
        'wizard/hr_expense_refuse_reason_views.xml',
        'views/hr_expense_views.xml',
        'views/mail_activity_views.xml',
        'security/ir_rule.xml',
        'report/hr_expense_report.xml',
        'views/hr_department_views.xml',
        'views/assets.xml',
        'views/res_config_settings_views.xml',
        'views/account_journal_dashboard.xml',
    ],
    'demo': ['data/hr_expense_demo.xml'],
    'qweb': [
        "static/src/xml/documents_upload_views.xml",
        "static/src/xml/expense_dashboard.xml",
        "static/src/xml/expense_qr_modal_template.xml",
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
