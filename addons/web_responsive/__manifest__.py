{
    "name": "Web Responsive",
    "summary": "Responsive web client, community-supported",
    "version": "25.0.1.2.2",
    "category": "Website",
    "license": "LGPL-3",
    "installable": True,
    "auto_install": True,
    "depends": ["web", "mail"],
    "data": ["views/assets.xml", "views/res_users.xml", "views/web.xml"],
    "qweb": [
        "static/src/xml/apps.xml",
        "static/src/xml/form_buttons.xml",
        "static/src/xml/menu.xml",
        "static/src/xml/navbar.xml",
        "static/src/xml/attachment_viewer.xml",
        "static/src/xml/discuss.xml",
        "static/src/xml/control_panel.xml",
        "static/src/xml/search_panel.xml",
    ],
    "sequence": 1,
}
