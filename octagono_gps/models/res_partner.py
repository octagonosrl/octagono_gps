# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'
    Cuenta_GPS = fields.Char(string='Cuenta GPS')
    octagono_gps_count = fields.Integer(compute='_compute_octagono_gps_count', string='# of Vehiculos')
    # octagono_gps_ids = fields.One2many('octagono.gps', 'partner_id', 'Octagono GPS')

    def _compute_octagono_gps_count(self):
        octagono_data = self.env['octagono.gps']. \
            read_group(domain=[('partner_id', 'child_of', self.ids)], fields=['partner_id'], groupby=['partner_id'])
        # read to keep the child/parent relation while aggregating the read_group result in the loop
        partner_child_ids = self.read(['child_ids'])
        mapped_data = dict([(m['partner_id'][0], m['partner_id_count']) for m in octagono_data])
        for partner in self:
            # let's obtain the partner id and all its child ids from the read up there
            item = next(p for p in partner_child_ids if p['id'] == partner.id)
            partner_ids = [partner.id] + item.get('child_ids')
            # then we can sum for all the partner's child
            partner.octagono_gps_count = sum(mapped_data.get(child, 0) for child in partner_ids)
