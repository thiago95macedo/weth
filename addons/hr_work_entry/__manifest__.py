#-*- coding:utf-8 -*-

{
    'name': 'Work Entries',
    'category': 'Human Resources/Employees',
    'sequence': 39,
    'summary': 'Manage work entries',
    'description': "",
    'installable': True,
    'depends': [
        'hr',
    ],
    'data': [
        'security/hr_work_entry_security.xml',
        'security/ir.model.access.csv',
        'data/hr_work_entry_data.xml',
        'views/hr_work_entry_views.xml',
        'views/resource_views.xml',
    ],
    'qweb': [
        "static/src/xml/work_entry_templates.xml",
    ],
    'license': 'LGPL-3',
}
