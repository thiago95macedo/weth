{
    'name': 'Website profile',
    'category': 'Hidden',
    'version': '1.0',
    'summary': 'Access the website profile of the users',
    'description': "Allows to access the website profile of the users and see their statistics (karma, badges, etc..)",
    'depends': [
        'website_partner',
        'gamification'
    ],
    'data': [
        'data/profile_data.xml',
        'views/gamification_badge_views.xml',
        'views/website_profile.xml',
        'security/ir.model.access.csv',
    ],
    'auto_install': False,
    'license': 'LGPL-3',
}
