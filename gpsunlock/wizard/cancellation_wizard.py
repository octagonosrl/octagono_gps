# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import api, fields, models, _
from datetime import datetime


class CancellationWizard(models.TransientModel):
    _name = "cancellation.wizard"

    @api.model
    def default_get(self, fields):
        result = super(CancellationWizard, self).default_get(fields)
        if self._context.get('active_id'):
            gps = self.env['octagono.gps'].browse([self._context.get('active_id')])
            result['vehicle_id'] = gps.id
        return result

    vehicle_id = fields.Many2one('octagono.gps', 'Vehiculo', readonly="1",store=True, required=True)
    cancellation_reason = fields.Selection([('vehicle_change', 'Cambio de Vehiculo'), ('warranty', 'Garantia'),
                                            ('owner_change', 'Cambio de Dueño'), ('repair', 'Vehiculo en Reparacion'),
                                            ('contract_end', 'Finalizacion de Contrato')],
                                           string="Motivo de Cancelacion",required=True)
    cancel_date = fields.Datetime(string="Fecha de Cancelación", readonly="1", default=datetime.today())

    @api.multi
    def return_action(self):

        vehicle = self.vehicle_id
       
        cancellation = self.env['cancellation.gps'].create({'vehicle_id': vehicle.id, 'cancellation_reason': self.cancellation_reason, 'cancel_date': self.cancel_date})
        vehicle.last_cancellation = self.cancellation_reason
        vehicle._create_returns()