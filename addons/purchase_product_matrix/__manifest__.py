{
    'name': "Purchase Matrix",
    'summary': """
       Add variants to your purchase orders through an Order Grid Entry.
    """,
    'description': """
        This module allows to fill Purchase Orders rapidly
        by choosing product variants quantity through a Grid Entry.
    """,
    'category': 'Inventory/Purchase',
    'version': '1.0',
    'depends': ['purchase', 'product_matrix'],
    'data': [
        'views/assets.xml',
        'views/purchase_views.xml',
        'report/purchase_quotation_templates.xml',
        'report/purchase_order_templates.xml',
    ],
    'license': 'LGPL-3',
}
