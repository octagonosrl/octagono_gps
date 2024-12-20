# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class StockLocationRoute(models.Model):
    _inherit = "stock.location.route"
    octagono_selectable = fields.Boolean("Selectable on Octagono GPS Line")


class StockMove(models.Model):
    _inherit = "stock.move"
    octagono_line_id = fields.Many2one('octagono.gps.line', 'Octagono Line')

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super(StockMove, self)._prepare_merge_moves_distinct_fields()
        distinct_fields += ['octagono_line_id']
        return distinct_fields

    @api.model
    def _prepare_merge_move_sort_method(self, move):
        move.ensure_one()
        keys_sorted = super(StockMove, self)._prepare_merge_move_sort_method(move)
        keys_sorted.append(move.octagono_line_id.id)
        return keys_sorted

    def _prepare_extra_move_vals(self, qty):
        vals = super(StockMove, self)._prepare_extra_move_vals(qty)
        vals['octagono_line_id'] = self.octagono_line_id.id
        return vals

    def _prepare_move_split_vals(self, uom_qty):
        vals = super(StockMove, self)._prepare_move_split_vals(uom_qty)
        vals['octagono_line_id'] = self.octagono_line_id.id
        return vals

    def _action_done(self):
        result = super(StockMove, self)._action_done()
        for line in result.mapped('octagono_line_id').sudo():
            line.qty_delivered = line._get_delivered_qty()
        return result

    @api.model
    def write(self, vals):
        res = super(StockMove, self).write(vals)
        if 'product_uom_qty' in vals:
            for move in self:
                if move.state == 'done':
                    octagono_order_lines = self.filtered(
                        lambda move: move.octagono_line_id and move.product_id.expense_policy == 'no'). \
                        mapped('octagono_line_id')
                    for line in octagono_order_lines.sudo():
                        line.qty_delivered = line._get_delivered_qty()
        return res


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    octagono_id = fields.Many2one('octagono.gps', 'Octagono GPS')


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        result = super(StockRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id,
                                                                     name, origin, values, group_id)
        if values.get('octagono_line_id', False):
            result['octagono_line_id'] = values['octagono_line_id']
        return result


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    octagono_id = fields.Many2one('octagono.gps', 'Octagono GPS', related='move_lines.octagono_line_id.order_id',
                                  readonly=True, store=True)


class ReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def _prepare_move_default_values(self, return_line, new_picking):
        vals = super(ReturnPicking, self)._prepare_move_default_values(return_line, new_picking)
        vals['octagono_line_id'] = return_line.move_id.octagono_line_id.id
        return vals
