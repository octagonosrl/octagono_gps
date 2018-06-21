# -*- coding: utf-8 -*-
{
    'name': "GPS",
    'summary': "Manejo de registros de GPS",
    'description': """
    Description the module.
    """,
    'version': "1.0",
    'category': "",
    'depends': ['sales_team', 'account', 'portal', 'hr', 'stock'],
    'data': [
        'security/octagono_gps_groups.xml',
        'security/ir.model.access.csv',
        'views/octagono_views.xml',
        'views/octagono_model_views.xml',
        'views/product_views.xml',
        'views/res_partner_views.xml',
        'views/stock_views.xml',
    ],
    'demp': [],
    'application': True,
    'installable': True,
}
