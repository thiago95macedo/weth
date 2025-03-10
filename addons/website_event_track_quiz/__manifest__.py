
{
    'name': 'Quizzes on Tracks',
    'category': 'Marketing/Events',
    'sequence': 1007,
    'version': '1.0',
    'summary': 'Quizzes on tracks',
    'website': 'https://www.weth.com.br/page/events',
    'description': "",
    'depends': [
        'website_profile',
        'website_event_track',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/event_leaderboard_templates.xml',
        'views/event_quiz_views.xml',
        'views/event_quiz_question_views.xml',
        'views/event_track_views.xml',
        'views/event_track_visitor_views.xml',
        'views/event_menus.xml',
        'views/event_quiz_templates.xml',
        'views/event_track_templates_page.xml',
        'views/event_event_views.xml',
        'views/event_type_views.xml'
    ],
    'demo': [
        'data/quiz_demo.xml',
    ],
    'application': False,
    'installable': True,
    'license': 'LGPL-3',
}
