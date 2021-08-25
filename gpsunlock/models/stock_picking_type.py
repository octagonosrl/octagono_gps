
from odoo import models, fields


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    is_for_gps_return = fields.Boolean('Tipo de operación para retorno de GPS')
