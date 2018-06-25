# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def _octagono_count(self):
        for product in self:
            product.octagono_count = sum([p.octagono_count for p in product.product_variant_ids])

    @api.multi
    def action_view_octagono(self):
        self.ensure_one()
        action = self.env.ref('octagono_gps.action_product_octagono_list')
        product_ids = self.with_context(active_test=False).product_variant_ids.ids

        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': "{'default_product_id': " + str(product_ids[0]) + "}",
            'res_model': action.res_model,
            'domain': [('state', 'in', ['octagono', 'done']), ('product_id.product_tmpl_id', '=', self.id)],
        }

    octagono_count = fields.Integer(compute='_octagono_count', string='# Vehiculos')
    octagono_ok = fields.Boolean(string='Puede ser tratado en GPS', default=False)

    description_octagono = fields.Text(
        'Octagono Description', translate=True,
        help="A description of the Product that you want to communicate to your customers. "
             "This description will be copied to every Sales Order, Delivery Order and Customer Invoice/Credit Note")

    invoice_policy = fields.Selection(
        [('order', 'Ordered quantities'),
         ('delivery', 'Delivered quantities'),
         ], string='Invoicing Policy',
        help='Ordered Quantity: Invoice based on the quantity the customer ordered.\n'
             'Delivered Quantity: Invoiced based on the quantity the vendor delivered (time or deliveries).',
        default='order')
