# octagono_gps/hooks.py

from odoo import api, SUPERUSER_ID

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['ir.config_parameter'].set_param('group_stock_production_lot', '1')
