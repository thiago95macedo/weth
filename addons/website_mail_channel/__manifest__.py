{
    'name': 'Website Mail Channels',
    'category': 'Website/Website',
    'summary': 'Allow visitors to join public mail channels',
    'description': """
Visitors can join public mail channels managed in the Discuss app in order to get regular updates or reach out with your community.
    """,
    'depends': ['website_mail'],
    'data': [
        'data/mail_template_data.xml',
        'views/assets.xml',
        'views/snippets/s_channel.xml',
        'views/snippets/snippets.xml',
        'views/website_mail_channel_templates.xml',
    ],
    'license': 'LGPL-3',
}
