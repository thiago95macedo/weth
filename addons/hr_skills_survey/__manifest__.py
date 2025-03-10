{
    'name': 'Skills Certification',
    'category': 'Hidden',
    'version': '1.0',
    'summary': 'Add certification to resumé of your employees',
    'description':
        """
Certification and Skills for HR
===============================

This module adds certification to resumé for employees.
        """,
    'depends': ['hr_skills', 'survey'],
    'data': [
        'views/hr_templates.xml',
        'data/hr_resume_data.xml',
    ],
    'qweb': [
        'static/src/xml/resume_templates.xml',
    ],
    'auto_install': True,
    'license': 'LGPL-3',
}
