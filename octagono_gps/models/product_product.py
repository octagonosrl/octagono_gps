# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'


    def _octagono_count(self):
        domain = [
            ('state', 'in', ['registered', 'done']),
            ('product_id', 'in', self.mapped('id')),
        ]
        octagono_gps_line = self.env['octagono.gps.line'].search(domain)
        for product in self:
            product.octagono_count = len(
                octagono_gps_line.filtered(lambda r: r.product_id == product).mapped('order_id'))

    octagono_count = fields.Integer(compute='_octagono_count', string='# Vehiculos')
    octagono_ok = fields.Boolean('Puede ser tratado en GPS', related="product_tmpl_id.octagono_ok", store=True)
