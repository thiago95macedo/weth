{
    'name': "HR Attendance Holidays",
    'summary': """""",
    'category': 'Human Resources',
    'description': """
Hides the attendance presence button when an employee is on leave.
    """,
    'version': '1.0',
    'depends': ['hr_attendance', 'hr_holidays'],
    'auto_install': True,
    'data': [
        'views/hr_employee_views.xml',
    ],
    'license': 'LGPL-3',
}
