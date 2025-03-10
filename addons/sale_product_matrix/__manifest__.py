{
    'name': "Sale Matrix",
    'summary': "Add variants to Sales Order through a grid entry.",
    'description': """
        This module allows to fill Sales Order rapidly
        by choosing product variants quantity through a Grid Entry.
    """,
    'category': 'Sales/Sales',
    'version': '1.0',
    'depends': ['sale', 'product_matrix', 'sale_product_configurator'],
    'data': [
        'views/assets.xml',
        'views/product_template_views.xml',
        'views/sale_views.xml',
        'report/sale_report_templates.xml',
    ],
    'demo': [
        'data/product_matrix_demo.xml'
    ],
    'license': 'LGPL-3',
}
