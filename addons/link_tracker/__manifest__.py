{
    'name': 'Link Tracker',
    'category': 'Marketing',
    'description': """
Shorten URLs and use them to track clicks and UTMs
""",
    'version': '1.1',
    'depends': ['utm', 'mail'],
    'data': [
        'views/link_tracker_views.xml',
        'views/utm_campaign_views.xml',
        'security/ir.model.access.csv',
    ],
    'license': 'LGPL-3',
}
