# -*- coding: utf-8 -*-
{
    'name': "GPS",
    'summary': "Manejo de registros de GPS",
    'description': """
    Description the module.
    """,
    'version': "1.0",
    'category': "Human Resources",
    'depends': ['base', 'mail', 'account', 'portal', 'hr', 'stock','stock_account'],
    'data': [
        'security/octagono_gps_groups.xml',
        'security/ir.model.access.csv',
        'views/octagono_views.xml',
        'views/octagono_model_views.xml',
        'views/product_views.xml',
        'views/res_partner_views.xml',
        'views/stock_views.xml',
        'views/stock_picking_relation.xml',
        'data/gps_cars_data.xml',
        'data/gps_data.xml',
        'data/gps_colors_data.xml',
       # 'data/stock_config_settings.xml',
        'views/account_invoice_tree.xml',
    ],
    'demo': [],
    'application': True,
    'installable': True,
    'post_init_hook': 'post_init_hook',
}
