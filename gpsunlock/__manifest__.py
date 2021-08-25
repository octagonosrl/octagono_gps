# -*- coding: utf-8 -*-
{
    'name': "Octagono Retornos",

    'summary': """
       """,

    'description': """
       
    """,

    'author': "Risbelly Carvajal - Octagono SRL",
    'website': "http://www.octagono.com.do",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'octagono_gps', 'stock'],

    # always loaded
    'data': [
        'wizard/coordinate_wizard_view.xml',
        'wizard/cancellation_wizard_view.xml',
        'views/views.xml',
        'views/invibuttons.xml',
        'views/stock_picking_type_views.xml',
        # 'static/src/js/gpsunlock.js',
    ],
    'images': ['static/image/loader_car.gif'],
}