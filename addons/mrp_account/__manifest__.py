{
    'name': 'Accounting - MRP',
    'version': '1.0',
    'category': 'Manufacturing/Manufacturing',
    'summary': 'Analytic accounting in Manufacturing',
    'description': """
Analytic Accounting in MRP
==========================

* Cost structure report

Also, allows to compute the cost of the product based on its BoM, using the costs of its components and work center operations.
It adds a button on the product itself but also an action in the list view of the products.
If the automated inventory valuation is active, the necessary accounting entries will be created.

""",
    'website': 'https://www.weth.com.br/page/manufacturing',
    'depends': ['mrp', 'stock_account'],
    "init_xml" : [],
    "demo_xml" : [],
    "data": [
        'security/ir.model.access.csv',
        "views/product_views.xml",
        "views/mrp_production_views.xml",
    ],
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
