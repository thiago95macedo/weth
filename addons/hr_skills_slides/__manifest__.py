{
    'name': 'Skills e-learning',
    'category': 'Hidden',
    'version': '1.0',
    'summary': 'Add completed courses to resumé of your employees',
    'description':
        """
E-learning and Skills for HR
============================

This module add completed courses to resumé for employees.
        """,
    'depends': ['hr_skills', 'website_slides'],
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
