# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class StockLocationRoute(models.Model):
    _inherit = "stock.location.route"
    octagono_selectable = fields.Boolean("Selectable on Sales Order Line")


class StockMove(models.Model):
    _inherit = "stock.move"
    octagono_line_id = fields.Many2one('octagono.gps.line', 'Octagono Line')

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        _logger.info('_prepare_merge_moves_distinct_fields %s', self._name)
        distinct_fields = super(StockMove, self)._prepare_merge_moves_distinct_fields()
        distinct_fields += ['octagono_line_id']
        return distinct_fields

    @api.model
    def _prepare_merge_move_sort_method(self, move):
        _logger.info('_prepare_merge_move_sort_method %s', self._name)
        move.ensure_one()
        keys_sorted = super(StockMove, self)._prepare_merge_move_sort_method(move)
        keys_sorted.append(move.octagono_line_id.id)
        return keys_sorted

    def _action_done(self):
        _logger.info('_action_done %s', self._name)
        result = super(StockMove, self)._action_done()
        for line in result.mapped('octagono_line_id').sudo():
            line.qty_delivered = line._get_delivered_qty()
        return result

    @api.multi
    def write(self, vals):
        _logger.info('write %s', self._name)
        res = super(StockMove, self).write(vals)
        if 'product_uom_qty' in vals:
            for move in self:
                if move.state == 'done':
                    octagono_order_lines = self.filtered(
                        lambda move: move.octagono_line_id and move.product_id.expense_policy == 'no').mapped(
                        'octagono_line_id')
                    for line in octagono_order_lines.sudo():
                        line.qty_delivered = line._get_delivered_qty()
                        _logger.info('%s, %s', self._name, line.qty_delivered)
        return res


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    octagono_id = fields.Many2one('octagono.order', 'Octagono Order')


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        result = super(ProcurementRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id,
                                                                     name, origin, values, group_id)
        if values.get('octagono_line_id', False):
            result['octagono_line_id'] = values['octagono_line_id']
        return result


# copy
class StockPicking(models.Model):
    _inherit = 'stock.picking'

    octagono_id = fields.Many2one('octagono.gps', 'Octagono GPS', related='move_lines.octagono_line_id.order_id',
                                  readonly=True, store=True)
