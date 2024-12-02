# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    octagono_gps_count = fields.Integer(compute='_compute_octagono_gps_count', string='# of Vehiculos')
    octagono_gps_ids = fields.One2many('octagono.gps', 'partner_id', 'Octagono GPS')
    x_studio_field_ddQ6z = fields.Char('Cuenta')
    x_studio_field_9ulTy = fields.Date('Fecha de nacimiento')
    x_studio_field_eQPah = fields.Boolean('Copia Cedula')
    x_studio_field_F8goH = fields.Boolean('Contrato:')
    x_studio_field_PwPq3 = fields.Date('Administrador de la cuenta')
    x_studio_field_RReZ7 = fields.Char('Correo de notificación')
    x_studio_field_rYv4p = fields.Char('Fecha de Recepción:')
    x_studio_field_S2KYm = fields.Char('Observaciones:')
    zip = fields.Char('Zip')


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
