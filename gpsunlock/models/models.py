
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero
import time
from datetime import datetime


class OctagonoGps(models.Model):
    _inherit = 'octagono.gps'

    cancel_date = fields.Date(string="Fecha de Cancelación")
    cancellation_reason = fields.Selection([
        ('vehicle_change', 'Cambio de Vehiculo'),
        ('warranty', 'Garantia'),
        ('owner_change', 'Cambio de Dueño'),
        ('account_change', 'Cambio de Cuenta'),
        ('repair', 'Vehiculo en Reparacion'),
        ('contract_end', 'Finalizacion de Contrato'),
        ('lost_device', 'Equipo Perdido'),
        ('contract_end_lost_device', 'Finalización de contrato / Equipo Perdido')
    ], string="Motivo de Cancelacion")

    @api.multi
    def _prepare_move_default_values(self, return_line, new_picking):
        vals = {
            'product_id': return_line.product_id.id,
            'product_uom_qty': return_line.quantity,
            'product_uom': return_line.product_id.uom_id.id,
            'picking_id': new_picking.id,
            'state': 'draft',
            'location_id': return_line.move_id.location_dest_id.id,
            'location_dest_id': self.location_id.id or return_line.move_id.location_id.id,
            'picking_type_id': new_picking.picking_type_id.id,
            'warehouse_id': self.picking_ids[0].picking_type_id.warehouse_id.id,
            'origin_returned_move_id': return_line.move_id.id,
            'procure_method': 'make_to_stock',
        }
        return vals

    def _create_returns(self, cancellation_reason):
        # create new picking for returned products
        lot = {}
        lines = []

        picking_type_id = self.picking_ids[0].picking_type_id.return_picking_type_id.id or self.picking_ids[0].picking_type_id.id

        for line in self.order_line:
            lot[str(line.product_id.id)] = line.product_lot_id.id
            lines.append((0, 0, {
                        'partner_id': self.partner_id.id,
                        'product_id': line.product_id.id,
                        'product_lot_id': line.product_lot_id.id,
                        'name': line.product_id.name,
                        'product_uom': line.product_id.uom_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'quantity_done': line.qty_delivered,
                        'octagono_line_id': line.id,
                        'order_id': self.id,
             }))

        new_picking = self.picking_ids[0].copy({
            'move_lines': lines,
            'picking_type_id': picking_type_id,
            'state': 'draft',
            'origin': _("Return of %s") % self.picking_ids[0].name,
            'location_id': self.picking_ids[0].location_dest_id.id,
            'location_dest_id': self.picking_ids[0].location_id.id})
        new_picking.message_post_with_view('mail.message_origin_link',
            values={'self': new_picking, 'origin': self.picking_ids[0]},
            subtype_id=self.env.ref('mail.mt_note').id)
        for line in new_picking.move_lines:
            line.move_line_ids[0].write({'lot_id': lot[str(line.product_id.id)]})


        # new_picking.move_lines[0].move_line_ids[0].write({'lot_id': lot[0]})
        # new_picking.move_lines[1].move_line_ids[0].write({'lot_id': lot[1]})

        now = datetime.now().strftime("%Y%m%d%H%M%S")  # obtener la fecha en formato yyyymmddhhiiss
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.vin_sn:
            self.vin_sn = self.vin_sn + "-" + now
        else:
            raise UserError("El chasis esta vacío, por favor rellenar.")
        self.cancel_date = date
        self.cancellation_reason = cancellation_reason

        # new_picking.action_confirm()
        new_picking.action_assign()
        new_picking.button_validate()

        self.state = 'cancel'

    def create_returns(self):
        view = self.env.ref('gpsunlock.cancellation_wizard_view')
        context = dict(self._context or {})

        return {
            'name': 'Devolvera los productos asignados y creara un nuevo conduce',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cancellation.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }
