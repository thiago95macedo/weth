{
    'name': 'Online Members Directory',
    'category': 'Website/Website',
    'summary': 'Publish your members directory',
    'version': '1.0',
    'description': """
Publish your members/association directory publicly.
    """,
    'depends': ['website_partner', 'website_google_map', 'association', 'website_sale'],
    'data': [
        'views/product_template_views.xml',
        'views/website_membership_templates.xml',
        'security/ir.model.access.csv',
        'security/website_membership.xml',
    ],
    'demo': ['data/membership_demo.xml'],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'license': 'LGPL-3',
}
