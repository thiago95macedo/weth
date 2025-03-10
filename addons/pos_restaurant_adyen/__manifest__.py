{
    'name': 'POS Restaurant Adyen',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'summary': 'Adds American style tipping to Adyen',
    'description': '',
    'depends': ['pos_adyen', 'pos_restaurant', 'payment_adyen'],
    'data': [
        'views/pos_payment_method_views.xml',
        'views/point_of_sale_assets.xml',
    ],
    'auto_install': True,
    'license': 'LGPL-3',
}
