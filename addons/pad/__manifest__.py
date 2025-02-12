{
    'name': 'Collaborative Pads',
    'version': '2.0',
    'category': 'Hidden/Tools',
    'description': """
Adds enhanced support for (Ether)Pad attachments in the web client.
===================================================================

Lets the company customize which Pad installation should be used to link to new
pads (by default, http://etherpad.com/).
    """,
    'depends': ['web', 'base_setup'],
    'data': [
        'views/pad.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': ['data/pad_demo.xml'],
    'web': True,
    'qweb': ['static/src/xml/pad.xml'],
    'license': 'LGPL-3',
}
