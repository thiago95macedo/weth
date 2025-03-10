{
    'name': "Sale Product Configurator",
    'version': '1.0',
    'category': 'Hidden',
    'summary': "Configure your products",

    'description': """
Technical module installed when the user checks the "module_sale_product_configurator" setting.
The main purpose is to override the sale_order view to allow configuring products in the SO form.

It also enables the "optional products" feature.
    """,

    'depends': ['sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/templates.xml',
        'views/sale_views.xml',
        'wizard/sale_product_configurator_views.xml',
    ],
    'demo': [
        'data/sale_demo.xml',
    ],
    'license': 'LGPL-3',
}
