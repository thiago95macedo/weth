{
    'name': 'Product Availability',
    'category': 'Website/Website',
    'summary': 'Manage product inventory & availability',
    'description': """
Manage the inventory of your products and display their availability status in your eCommerce store.
In case of stockout, you can decide to block further sales or to keep selling.
A default behavior can be selected in the Website settings.
Then it can be made specific at the product level.
    """,
    'depends': [
        'website_sale',
        'sale_stock',
    ],
    'data': [
        'views/product_template_views.xml',
        'views/res_config_settings_views.xml',
        'views/website_sale_stock_templates.xml',
        'views/stock_picking_views.xml'
    ],
    'demo': [
        'data/website_sale_stock_demo.xml',
    ],
    'auto_install': True,
    'license': 'LGPL-3',
}
