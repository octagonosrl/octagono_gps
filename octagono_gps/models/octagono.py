# -*- coding: utf-8 -*-
import logging
import datetime as _date
from datetime import datetime, timedelta, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

# from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_compare, float_round, float_is_zero

_logger = logging.getLogger(__name__)


class OctagonoGPS(models.Model):
    _name = 'octagono.gps'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "GPS"
    _order = 'date_order desc, id desc'
    _sql_constraints = [
        ('octagono_gps_vin_sn_unique', 'unique(vin_sn)', 'La numeracion del chasis ya existe.')
    ]
    account = fields.Char(related="partner_id.cuenta_gps", store=True)

    @api.model
    # def get_empty_list_help(self, help):
    #     if help:
    #         return '<p class=''oe_view_nocontent_create''">%s</p>' % (help)
    #     return super(OctagonoGPS, self).get_empty_list_help(help)
    def get_empty_list_help(self, help):
        if help:
            return "<p class='oe_view_nocontent_create'>{}</p>".format(help)
        return super().get_empty_list_help(help)

    @api.model
    def _default_note(self):
        return self.env.user.company_id.octagono_note or ''

    @api.depends('fiscal_position_id')
    def _compute_tax_id(self):
        for order in self:
            if order.order_line.filtered(lambda l: l.tax_id):
                order.order_line._compute_tax_id()

    @api.model
    def _default_warehouse_id(self):
        company = self.env.user.company_id
        if company:
            warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
            return warehouse.id if warehouse else False
        return False

    name = fields.Char(string='Referencia', compute='_compute_name', store=True)
    origin = fields.Char(string='Documento fuente', help="Referencia del documento que generó esta solicitud "
                                                         "de orden de regstro de vehiculo.")
    client_order_ref = fields.Char(string='Customer Reference', copy=False)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('sent', 'Registro Enviado'),
        ('registered', 'Registrado'),
        ('done', 'Asignado'),
        ('assigned', 'Producto Asignado'),
        ('valid_product', 'Producto Validado'),
        ('suspended', 'Suspendido'),
        ('cancel', 'Cancelado'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=True, default='draft')
    # date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    # validity_date = fields.Date(string='Expiration Date', readonly=True, copy=False, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
    #                             help="Manually set the expiration date of your quotation (offer), or it will set the "
    #                                  "date automatically based on the template if online quotation is installed.")
    # is_expired = fields.Boolean(compute='_compute_is_expired', string="Is expired")
    # create_date = fields.Datetime(string='Creation Date', readonly=True, index=True, help="Date on which sales order is created.")
    # confirmation_date = fields.Datetime(string='Fecha de confirmación', readonly=True, index=True, copy=False,
    #                                     help=u"Fecha de confirmación.")
    # billing_date = fields.Datetime(string='Fecha de facturación', index=True)
    # next_billing_date = fields.Datetime(string='Próxima fecha de factura', index=True)
    user_id = fields.Many2one('res.users', string='Usuario', index=True, tracking=True,
                              default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Propetario', required=True, change_default=True, index=True, tracking=True)
    # partner_name = fields.Char(related='partner_id.name')
    # partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address', readonly=True, required=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Invoice address for current sales order.")
    # partner_shipping_id = fields.Many2one('res.partner', string='Dirección de entrega', readonly=True, required=True,  states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Delivery address for current sales order.")
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Pricelist for current sales order.")
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True, required=True, store=True)
    # order_line = fields.One2many('octagono.gps.line', 'order_id', string='Order Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    # note = fields.Text('Nota', default=_default_note, tracking=True)
    # payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')
    # fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position')
    # company_id = fields.Many2one('res.company', 'Empresa', default=lambda self: self.env.company)
    # product_id = fields.Many2one('product.product', related='order_line.product_id', string='Product', store=True)
    # # product_lot_id = fields.Many2one('stock.production.lot', related='order_line.product_lot_id', string='Serial del producto', store=True)
    # gps_id = fields.Many2one('product.product', compute='_get_product_lots', string='GPS', store=True)
    # gps_lot_id = fields.Many2one('stock.production.lot', compute='_get_product_lots', string='Serial GPS', store=True)
    # sim_id = fields.Many2one('product.product', compute='_get_product_lots', string='SIM', store=True)
    # sim_lot_id = fields.Many2one('stock.production.lot', compute='_get_product_lots', string='Serial SIM', store=True)

    @api.depends('order_line', 'order_line.product_id', 'order_line.product_lot_id')
    def _get_product_lots(self):
        for rec in self:
            gps_line = rec.order_line.filtered(lambda line: 'GPS' in line.product_id.name)
            sim_line = rec.order_line.filtered(lambda line: 'SIM' in line.product_id.name)

            rec.gps_id = gps_line[0].product_id.id if gps_line else False
            rec.gps_lot_id = gps_line[0].product_lot_id.id if gps_line else False
            rec.sim_id = sim_line[0].product_id.id if sim_line else False
            rec.sim_lot_id = sim_line[0].product_lot_id.id if sim_line else False

    # Campo relacionados a vehiculos
    active = fields.Boolean(default=True, tracking=True)
    blocking_type = fields.Selection(selection=[('b0', 'B0'), ('b1', 'B1'), ('b2', 'B2'), ('b3', 'B3')], string="Tipo de bloqueo")
    color = fields.Many2one('octagono.gps.colors', tracking=True)
    driver = fields.Char('Responsable', tracking=True)
    image = fields.Binary(related='model_id.image', string="Logo", store=True)
    # image_medium = fields.Binary(related='model_id.image_medium', string="Logo (medium)", store=True)
    # image_small = fields.Binary(related='model_id.image_small', string="Logo (small)", store=True)
    license_plate = fields.Char('Matricula', tracking=True, help="Numero de matriculo o placa del vehiculo")
    install_date = fields.Datetime(string=u"Fecha de instalación", index=True, default=lambda self: fields.Datetime.now(), tracking=True)
    installer_id = fields.Many2one('hr.employee', "Instalador", domain="[('department_id.name', 'in', ['Operaciones', 'operaciones'])]", tracking=True)
    model_id = fields.Many2one('octagono.model', "Modelo", help="Model of the vehicle", tracking=True)
    model_year = fields.Selection(selection='gen_date_select', string="Año del modelo", tracking=True)
    vin_sn = fields.Char("Num. Chasis", tracking=True)
    incoterm = fields.Many2one(
        'stock.incoterms', 'Incoterms',
        help="International Commercial Terms are a series of predefined "
             "commercial terms used in international transactions.", tracking=True)
    picking_policy = fields.Selection([
        ('direct', 'Entregar cada producto cuando esté disponible'),
        ('one', 'Entregar todos los productos a la vez')],
        string='Shipping Policy', required=True, readonly=True, default='direct',
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, tracking=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, default=_default_warehouse_id, tracking=True)
    picking_ids = fields.One2many('stock.picking', 'octagono_id', string='Pickings')
    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_ids')
    procurement_group_id = fields.Many2one('procurement.group', 'Procurement Group', copy=False)
    is_waiting = fields.Boolean(compute="_compute_is_waiting")
    is_assign = fields.Boolean(compute="_compute_is_assign")
    p_installation = fields.Many2many('octagono.gps.tags', 'octagono_gps_tags_rel', string="P. Instalacion")
    select_period = fields.Selection([('monthly', 'Mensual'), ('annual', 'Anual'), ('biannual', 'BiAnual'), ('triannual', 'TriAnual')], index=True, default='monthly', tracking=True)
    phone_driver = fields.Char(string='Te. Responsable')
    num_conduce = fields.Char(string='Num. Conduce')

    def _compute_is_expired(self):
        now = datetime.now()
        for order in self:
            # if order.validity_date and fields.Datetime.from_string(order.validity_date) < now:
            if order.validity_date and order.validity_date < now:
                order.is_expired = True
            else:
                order.is_expired = False

    @api.model
    def _get_customer_lead(self, product_tmpl_id):
        return False


    def unlink(self):
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise UserError(_('You can not delete a sent quotation or a sales order! Try to cancel it before.'))
        # return super(OctagonoGPS, self).unlink()
        return super().unlink()



    @api.onchange('partner_shipping_id', 'partner_id')
    def onchange_partner_shipping_id(self):
        # self.fiscal_position_id = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id,
        #                                                                                   self.partner_shipping_id.id)
        self.fiscal_position_id = self.env['account.fiscal.position'].with_context(
            force_company=self.company_id.id
        ).get_fiscal_position(self.partner_id)
        return {}



    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        - Driver name
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'user_id': self.partner_id.user_id.id or self.env.uid,
            'driver': self.partner_id.display_name,
        }
        if self.env.user.company_id.octagono_note:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.user.company_id.octagono_note

        self.update(values)

    def validate_product(self, product_ids):
        """
        Esta funcion se encarga de validar la lineas de producto.
        :param product_ids:
        :return:
        """
        cat_gps = ['GPS', 'gps', 'Gps']
        cat_sim = ['sim card', 'Sim Card', 'SIM CARD']
        # validamos la existencia de las categorias de productos
        if not self.env['product.category'].search([('name', 'in', cat_sim)]):
            raise ValidationError('Categoria de producto Sim Card, no existe!')

        if not self.env['product.category'].search([('name', 'in', cat_gps)]):
            raise ValidationError('Categoria de producto GPS, no existe!')
        # validamos que la linea de productos asignados sea igual a 2
        if len(product_ids) < 2:
            raise ValidationError('Asegurse de asginar un Sim Card y un GPS al registro!')
        # nos aseguramos que los productos asignados sean de la categoria correctas
        count_sim = 0
        count_gps = 0
        for product_id in product_ids:
            product_obj = self.env['product.product'].browse([product_id])
            if product_obj.categ_id.name in cat_gps:
                count_gps += 1
                # si el producto gps fue asignado 2 veces error
                if count_gps == 2:
                    raise ValidationError('Minima asignacion del producto "{}" sobrepasada. \n'
                                          'Asegurese de asignar solo un gps y un sim card'.format(product_obj.name))
            elif product_obj.categ_id.name in cat_sim:
                count_sim += 1
                # si el producto sim fue asignado 2 veces error
                if count_sim == 2:
                    raise ValidationError('Minima asignacion del producto "{}" sobrepasada. \n'
                                          'Asegurese de asignar solo un gps y un sim card'.format(product_obj.name))
            else:
                raise ValidationError('Producto "%s" no es valido. \n'
                                      'Asegurese de seleccionar solo'
                                      ' un sim card y un gps.' % product_obj.name)

    @api.model
    def create(self, vals):
        if vals.get('order_line'):
            product_ids = [p[2]['product_id'] for p in vals['order_line']]
            self.validate_product(product_ids)

        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self._compute_name()

        # Se asegura de que se definan partner_invoice_id ',' partner_shipping_id 'y' pricelist_id '
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
            vals['pricelist_id'] = vals.setdefault('pricelist_id', partner.property_product_pricelist and partner.property_product_pricelist.id)

        return super(OctagonoGPS, self).create(vals)


    def copy_data(self, default=None):
        if default is None:
            default = {}
        if 'order_line' not in default:
            default['order_line'] = [(0, 0, line.copy_data()[0]) for line in
                                     self.order_line.filtered(lambda l: not l.is_downpayment)]
        # default['vin_sn'] = (self.vin_sn.split('-', 1))[0]
        default['vin_sn'] = (self.vin_sn.split('-', 1)[0]) if self.vin_sn else ''

        return super(OctagonoGPS, self).copy_data(default)


    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel', 'sent'])
        return orders.write({
            'state': 'draft',
        })


    def action_cancel(self):
        self.mapped('picking_ids').action_cancel()
        return self.write({'state': 'cancel'})



    def action_done(self):
        return self.write({'state': 'done'})


    def action_unlock(self):
        return self.write({'state': 'registered'})

    def _action_confirm(self):
        # for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
        #     order.message_subscribe([order.partner_id.id])
        for order in self:
            if order.partner_id.name in ('Operaciones', 'operaciones'):
                raise ValidationError('No puedes confirmar en el estado actual.')
        self.write({
            'state': 'registered',
            'confirmation_date': fields.Datetime.now()
        })
        # if self.env.context.get('send_email'):
        #     self.force_quotation_send()

        for order in self:
            order.order_line._action_launch_procurement_rule()

        return True


    def action_confirm(self):
        self._action_confirm()
        return True
    

    def toggle_suspension(self):
        if self.state == 'suspended':
            self.write({'state': 'done'})
        elif self.state == 'done':
            self.write({'state': 'suspended'})
        else:
            raise ValidationError('Solo puede utilizar este botón si el GPS está suspendido o asignado.')


    # observacion

    def _get_tax_amount_by_group(self):
        self.ensure_one()
        res = {}
        for line in self.order_line:
            price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
            taxes = line.tax_id.compute_all(price_reduce, quantity=line.product_uom_qty, product=line.product_id,
                                            partner=self.partner_shipping_id)['taxes']
            for tax in line.tax_id:
                group = tax.tax_group_id
                res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                for t in taxes:
                    if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                        res[group]['amount'] += t['amount']
                        res[group]['base'] += t['base']
        res = sorted(res.items(), key=lambda l: l[0].sequence)
        res = [(l[0].name, l[1]['amount'], l[1]['base'], len(res)) for l in res]
        return res

    # observacion

    def _notification_recipients(self, message, groups):
        groups = super(OctagonoGPS, self)._notification_recipients(message, groups)

        self.ensure_one()
        if self.state not in ('draft', 'cancel'):
            for group_name, group_method, group_data in groups:
                if group_name == 'customer':
                    continue
                group_data['has_button_access'] = True

        return groups

    @api.model
    def gen_date_select(self):
        select = []
        date_start = _date.date(1960, 1, 1)
        today = _date.date.today()
        for item in range(today.year - date_start.year + 2):
            date_id = date_label = str(date_start.year + item)
            select.append((date_id, date_label))
        select.reverse()
        return select

    @api.onchange('driver')
    def change_driver(self):
        if self.driver:
            self.driver = self.driver.title()

    @api.onchange('license_plate')
    def change_license_plate(self):
        if self.license_plate:
            self.license_plate = self.license_plate.upper()

    @api.constrains('order_line')
    @api.onchange('order_line')
    def _check_limit_order_line(self):
        while len(self.order_line) == 3:
            raise ValidationError("Maximo de productos alcansado, solo dos productos (sim card, gps)")

    @api.depends('model_id', 'license_plate')
    def _compute_name(self):
        name = _('New')
        for record in self:
            if not record.model_id and not record.license_plate:
                record.name = name
            elif record.model_id and not record.license_plate:
                record.name = name
            elif not record.model_id and record.license_plate:
                record.name = name
            else:
                name = [record.model_id.brand_id.name, record.model_id.name, record.license_plate]
                record.name = '/'.join(name)

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for order in self:
            order.delivery_count = len(order.picking_ids)

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        if self.warehouse_id.company_id:
            self.company_id = self.warehouse_id.company_id.id


    def action_view_delivery(self):
        """"
        Esta función devuelve una acción que muestra las órdenes de picking existentes de
        identificadores de órdenes de registros dados.
        Cuando solo se encuentre uno, muestre la selección de inmediato.
        """
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action

    @api.depends('picking_ids', 'picking_ids.state')
    def _compute_is_waiting(self):
        for order in self:
            if order.picking_ids and all([x.state in ['waiting', 'confirmed'] for x in order.picking_ids]):
                order.is_waiting = True
            else:
                order.is_waiting = False

    @api.depends('picking_ids', 'picking_ids.state')
    def _compute_is_assign(self):
        for order in self:
            if order.picking_ids and all([x.state in ['assigned', 'done'] for x in order.picking_ids]):
                order.is_assign = True
            else:
                order.is_assign = False


    @api.depends('picking_ids')
    def validate_picking(self):
        for picking in self.mapped('picking_ids'):
            picking.button_validate()
        self.update({'state': 'valid_product'})


    def action_assign_custom(self):
        assigned_moves = self.env['stock.move']
        partially_available_moves = self.env['stock.move']
        for move in self.order_line.mapped('move_ids').filtered(
                lambda m: m.state in ['confirmed', 'waiting', 'partially_available']):
            for order in self.mapped('order_line'):
                need = order.product_uom_qty
                available_quantity = self.env['stock.quant']._get_available_quantity(move.product_id, move.location_id,
                                                                                     order.product_lot_id)
                taken_quantity = move._update_reserved_quantity(need=need, available_quantity=available_quantity,
                                                                location_id=move.location_id,
                                                                lot_id=order.product_lot_id, strict=False)
                if need == taken_quantity:
                    assigned_moves |= move
                else:
                    partially_available_moves |= move
            partially_available_moves.write({'state': 'partially_available'})
            assigned_moves.write({'state': 'assigned'})
            self.mapped('picking_ids')._check_entire_pack()
            self.update({'state': 'assigned'})

    def action_picking_done(self):
        if self.order_line.mapped('move_ids').filtered(
                lambda m: m.state in ['confirmed', 'waiting', 'partially_available']):
            raise ValidationError('Asegurese de haber asignado los serial al movimiento.\n'
                                  'Ejecute el boton "ASIGNAR PRODUCTOS"')
        for move in self.order_line.mapped('move_ids'):
            for move_lines in move.mapped('move_line_ids'):
                move_lines.write({'qty_done': 1})
        self.validate_picking()
        self.action_done()

    def _update_line_message(self, subject=None, body=None, **kwargs):
        for order in self:
            order_lines = self.mapped('order_line')
            msg = "<b>" + kwargs.get('subtitle', 'Actualizando') + ".</b><ul>"
            for line in order_lines:
                msg += "<li> %s:" % (line.product_id.display_name,)
                msg += "<br/>" + _("Cantidad registrada") + ": %s -> %s <br/>" % (
                    line.product_uom_qty, float(body['product_uom_qty']),)
                if line.product_id.type in ('consu', 'product'):
                    msg += _("Cantidad entregada") + ": %s <br/>" % (line.qty_delivered,)
            msg += "</ul>"
            order.message_post(subject=subject, body=msg)


class OctagonoGPSLine(models.Model):
    _name = 'octagono.gps.line'
    _description = 'Octagono Order Line'
    _order = 'sequence, id'

    order_id = fields.Many2one('octagono.gps', string='Referencia', required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Text(string='Descripcion', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Taxes', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    price_reduce = fields.Float(compute='_get_price_reduce', string='Price Reduce', digits='Product Price', readonly=True, store=True)
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    price_reduce_taxinc = fields.Monetary(compute='_get_price_reduce_tax', string='Price Reduce Tax inc', readonly=True, store=True)
    price_reduce_taxexcl = fields.Monetary(compute='_get_price_reduce_notax', string='Price Reduce Tax excl', readonly=True, store=True)
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    product_id = fields.Many2one('product.product', string='Product', domain=[('octagono_ok', '=', True)], change_default=True, ondelete='restrict', required=True)
    product_lot_id = fields.Many2one('stock.production.lot', string='Serial del producto', change_default=True, ondelete='restrict', required=True)
    product_updatable = fields.Boolean(compute='_compute_product_updatable', string='Can Edit Product', readonly=True, default=True)
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    # Non-stored related field to allow portal user to see the image of the product he has ordered
    # product_image = fields.Binary('Product Image', related="product_id.image", store=True)
    qty_delivered_updateable = fields.Boolean(compute='_compute_qty_delivered_updateable', string='Can Edit Delivered', readonly=True, default=True)
    qty_delivered = fields.Float(string='Delivered', copy=False, digits='Product Unit of Measure', default=0.0)
    salesman_id = fields.Many2one(related='order_id.user_id', store=True, string='Usuario', readonly=True)
    currency_id = fields.Many2one(related='order_id.currency_id', store=True, string='Moneda', readonly=True)
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True)
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Propetario')
    is_downpayment = fields.Boolean(string="Is a down payment", help="Down payments are made when creating invoices "
                                                                     "from a sales order. They are not copied when "
                                                                     "duplicating a sales order.")
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('sent', 'Registro Enviado'),
        ('registered', 'Registrado'),
        ('done', 'Asignado'),
        ('assigned', 'Producto Asignado'),
        ('valid_product', 'Producto Validado'),
        ('suspended', 'Suspendido'),
        ('cancel', 'Cancelado'),
    ], related='order_id.state', string='Order Status', readonly=True, copy=False, store=True, default='draft')
    customer_lead = fields.Float('Delivery Lead Time', required=True, default=0.0,
                                 help="Número de días entre la confirmación del pedido y el envío de los productos al cliente")
    product_packaging = fields.Many2one('product.packaging', string='Package', default=False)
    route_id = fields.Many2one('stock.location.route', string='Route', domain=[('octagono_selectable', '=', True)], ondelete='restrict')
    move_ids = fields.One2many('stock.move', 'octagono_line_id', string='Stock Moves', readonly=True, ondelete='set null', copy=False)
    is_gps = fields.Boolean(default=False)

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.order_id.currency_id:  # Verifica que currency_id esté definido
                taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                                product=line.product_id, partner=line.order_id.partner_shipping_id)
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })
            # taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
            #                                 product=line.product_id, partner=line.order_id.partner_shipping_id)
            # line.update({
            #     'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
            #     'price_total': taxes['total_included'],
            #     'price_subtotal': taxes['total_excluded'],
            # })

    # @api.depends('product_id', 'order_id.state', 'qty_delivered')
    @api.depends('product_id', 'qty_delivered')
    def _compute_product_updatable(self):
        for line in self:
            if not line.move_ids.filtered(lambda m: m.state != 'cancel'):
                if line.state in ['done', 'cancel'] or (
                                line.state == 'registered' and line.qty_delivered > 0):
                    line.product_updatable = False
                else:
                    line.product_updatable = True
            else:
                line.product_updatable = False


    @api.depends('product_id.invoice_policy', 'order_id.state', 'product_id')
    def _compute_qty_delivered_updateable(self):
        # captar previamente el campo antes de filtrar
        self.mapped('product_id')
        # en productos consumibles o reutilizables, qty_delivered_updateable default
        # a Falso; en otras líneas use el cálculo original
        lines = self.filtered(lambda line: line.product_id.type not in ('consu', 'product'))
        lines = lines.with_prefetch(self._prefetch)
        for line in lines:
            line.qty_delivered_updateable = (line.order_id.state == 'registered') and (
                line.product_id.service_type == 'manual') and (line.product_id.expense_policy == 'no')

    @api.depends('price_unit', 'discount')
    def _get_price_reduce(self):
        for line in self:
            line.price_reduce = line.price_unit * (1.0 - line.discount / 100.0)

    @api.depends('price_total', 'product_uom_qty')
    def _get_price_reduce_tax(self):
        for line in self:
            line.price_reduce_taxinc = (
                float_round(line.price_total / line.product_uom_qty, precision_rounding=line.product_uom_qty.rounding)
                if line.product_uom_qty else 0.0
            )

    @api.depends('price_subtotal', 'product_uom_qty')
    def _get_price_reduce_notax(self):
        for line in self:
            line.price_reduce_taxexcl = (
                float_round(line.price_subtotal / line.product_uom_qty,
                            precision_rounding=line.product_uom_qty.rounding)
                if line.product_uom_qty else 0.0
            )

    # def _compute_tax_id(self):
    #     for line in self:
    #         fpos = line.order_id.fiscal_position_id or line.order_id.partner_id.property_account_position_id
    #         # Si se establece company_id, siempre filtre impuestos por la compañía
    #         taxes = line.product_id.taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
    #         line.tax_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_shipping_id) if fpos else taxes

    @api.depends('product_id', 'order_id.state', 'qty_delivered')
    def _compute_tax_id(self):
        for line in self:
            fpos = line.order_id.fiscal_position_id or line.order_id.partner_id.property_account_position_id
            taxes = line.product_id.taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
            if fpos:  # Verifica si fpos está definido
                line.tax_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_shipping_id) if fpos else taxes
            else:
                line.tax_id = taxes

    @api.model
    def _prepare_add_missing_fields(self, values):
        """ Deduce los campos obligatorios faltantes del cambio """
        res = {}
        onchange_fields = ['name', 'price_unit', 'product_uom', 'tax_id']
        if values.get('order_id') and values.get('product_id') and any(f not in values for f in onchange_fields):
            line = self.new(values)
            line.product_id_change()
            for field in onchange_fields:
                if field not in values:
                    res[field] = line._fields[field].convert_to_write(line[field], line)
        return res

    @api.model
    def create(self, values):
        values.update(self._prepare_add_missing_fields(values))
        line = super(OctagonoGPSLine, self).create(values)
        if line.order_id.state == 'registered':
            msg = _("Extra line with %s ") % (line.product_id.display_name,)
            line.order_id.message_post(body=msg)
            # si el state es registered invocamos la funcion encargada del movimiento de stock
            line._action_launch_procurement_rule()
        return line

    def _update_line_quantity(self, values):
        if self.mapped('qty_delivered') and  values.get('product_uom_qty', 0.0) < max(self.mapped('qty_delivered')):
            raise UserError('No puede disminuir la cantidad pedida por debajo de la cantidad entregada.\n'
                            'Crea una devolución primero.')
        for line in self:
            pickings = line.order_id.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))
            for picking in pickings:
                picking.message_post("La cantidad de %s ha sido actualizado desde %d to %d en %s" %
                                     (line.product_id.display_name, line.product_uom_qty, values['product_uom_qty'],
                                      line.order_id.name))
        orders = self.mapped('order_id')
        for order in orders:
            order_lines = self.filtered(lambda x: x.order_id == order)
            msg = "<b>La cantidad pedida ha sido actualizada.</b><ul>"
            for line in order_lines:
                msg += "<li> %s:" % (line.product_id.display_name,)
                msg += "<br/>" + _("Cantidad registrada") + ": %s -> %s <br/>" % (
                    line.product_uom_qty, float(values['product_uom_qty']),)
                if line.product_id.type in ('consu', 'product'):
                    msg += _("Cantidad entregada") + ": %s <br/>" % (line.qty_delivered,)
            msg += "</ul>"
            order.message_post(body=msg)


    def write(self, values):
        if 'product_uom_qty' in values:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            self.filtered(
                lambda r: r.state == 'registered' \
                          and float_compare(r.product_uom_qty, values['product_uom_qty'],
                                            precision_digits=precision) != 0)._update_line_quantity(values)

        # Evite escribir en un registro bloqueado.
        protected_fields = self._get_protected_fields()
        if 'done' in self.mapped('order_id.state') and any(f in values.keys() for f in protected_fields):
            protected_fields_modified = list(set(protected_fields) & set(values.keys()))
            fields = self.env['ir.model.fields'].search([
                ('name', 'in', protected_fields_modified), ('model', '=', self._name)
            ])
            raise UserError(
                _('Está prohibido modificar los siguientes campos en un registro Asignado:\n%s')
                % '\n'.join(fields.mapped('field_description'))
            )

        if 'product_uom_qty' in values:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            lines = self.filtered(
                lambda r: r.state == 'registered' and float_compare(r.product_uom_qty, values['product_uom_qty'],
                                                                    precision_digits=precision) == -1)

            lines._action_launch_procurement_rule()

        return super().write(values)


    def _prepare_procurement_values(self, group_id=False):
        """ Prepare una clave específica para movimientos u otros componentes que se crearán a partir
        de una regla de adquisición procedente de una línea de orden de venta. Este método podría anularse
        para agregar otra clave personalizada que podría ser utilizado en la creación de movimiento / po.
        """
        self.ensure_one()



        date_planned = fields.datetime.to_string(self.order_id.confirmation_date) \
                       + timedelta(days=self.customer_lead or 0.0)
        values = {
            'company_id': self.order_id.company_id,
            'group_id': group_id,
            'octagono_line_id': self.id,
            'date_planned': fields.Datetime.to_string(date_planned),
            'route_ids': self.route_id or self.order_id.warehouse_id.route_ids,
            'warehouse_id': self.order_id.warehouse_id or False,
            'partner_dest_id': self.order_id.partner_shipping_id
        }
        return values


    def _get_display_price(self, product):
        final_price, rule_id = self.order_id.pricelist_id.get_product_price_rule(self.product_id,
                                                                                 self.product_uom_qty or 1.0,
                                                                                 self.order_id.partner_id)
        context_partner = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order)
        base_price, currency_id = self.with_context(context_partner)._get_real_price_currency(self.product_id, rule_id,
                                                                                              self.product_uom_qty,
                                                                                              self.product_uom,
                                                                                              self.order_id.pricelist_id.id)
        if currency_id != self.order_id.pricelist_id.currency_id.id:
            base_price = self.env['res.currency'].browse(currency_id).with_context(context_partner).\
                compute(base_price, self.order_id.pricelist_id.currency_id)
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)


    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = 1.0

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        result = {'domain': domain}

        name = product.name_get()[0][1]
        if product.description_octagono:
            name += '\n' + product.description_octagono
        vals['name'] = name

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
                self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
        self.update(vals)

        return result

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product),
                                                                                      product.taxes_id, self.tax_id,
                                                                                      self.company_id)

    def name_get(self):
        result = []
        for so_line in self:
            name = '%s - %s' % (so_line.order_id.name, so_line.name.split('\n')[0] or so_line.product_id.name)
            if so_line.order_partner_id.ref:
                name = '%s (%s)' % (name, so_line.order_partner_id.ref)
            result.append((so_line.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if operator in ('ilike', 'like', '=', '=like', '=ilike'):
            args = expression.AND([
                args or [],
                ['|', ('order_id.name', operator, name), ('name', operator, name)]
            ])
        return super().name_search(name, args, operator, limit)


    def unlink(self):
        if self.filtered(lambda x: x.state in ('registered', 'done')):
            raise UserError(
                _('No puede eliminar una línea de orden de registro.\n'
                  'Descartar cambios e intentar configurar la cantidad en 0.'))
        return super().unlink()


    def _get_delivered_qty(self):
        self.ensure_one()
        qty = 0.0
        for move in self.move_ids.filtered(lambda r: r.state == 'done' and not r.scrapped):
            if move.location_dest_id.usage == "customer":
                if not move.origin_returned_move_id:
                    qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom)
            elif move.location_dest_id.usage != "customer" and move.to_refund:
                qty -= move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom)
        return qty

    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        """Recuperar el precio antes de aplicar la lista de precios
            :param obj product: objeto del registro actual del producto
            :parem float qty: cantidad total de producto
            :param tuple price_and_rule: tuple(price, suitable_rule) proveniente del cálculo de precios
            :param obj uom: unidad de medida de la línea de orden actual
            :param integer pricelist_id: Identificación de lista de precios del pedido de venta"""
        PricelistItem = self.env['product.pricelist.item']
        field_name = 'lst_price'
        currency_id = None
        product_currency = None
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
            if pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        product_currency = product_currency or (
            product.company_id and product.company_id.currency_id) or self.env.user.company_id.currency_id
        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(product_currency, currency_id)

        product_uom = self.env.context.get('uom') or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id.id

    def _get_protected_fields(self):
        return [
            'product_id', 'name', 'price_unit', 'product_uom', 'product_uom_qty',
            'tax_id', 'analytic_tag_ids'
        ]

    @api.onchange('product_id')
    def _onchange_product_id_set_customer_lead(self):
        self.customer_lead = self.product_id.sale_delay

    @api.onchange('product_id')
    def _onchange_product_id_uom_check_availability(self):
        if not self.product_uom or (self.product_id.uom_id.category_id.id != self.product_uom.category_id.id):
            self.product_uom = self.product_id.uom_id
        self._onchange_product_id_check_availability()

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        if not self.product_id or not self.product_uom_qty or not self.product_uom:
            self.product_packaging = False
            return {}
        if self.product_id.type == 'product':
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            product = self.product_id.with_context(warehouse=self.order_id.warehouse_id.id)
            product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)

            if float_compare(product.virtual_available, product_qty, precision_digits=precision) == -1:
                is_available = self._check_routing()
                if not is_available:
                    message = _('Usted planea asignar %s %s pero solo tienes %s %s disponible en %s almacén.') % \
                              (self.product_uom_qty, self.product_uom.name, product.virtual_available,
                               product.uom_id.name, self.order_id.warehouse_id.name)
                    # We check if some products are available in other warehouses.
                    if float_compare(product.virtual_available, self.product_id.virtual_available,
                                     precision_digits=precision) == -1:
                        message += _('\nExisten %s %s disponible en todos los almacenes.') % \
                                   (self.product_id.virtual_available, product.uom_id.name)

                    warning_mess = {
                        'title': _('No hay suficiente inventario!'),
                        'message': message
                    }
                    return {'warning': warning_mess}
        return {}

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        if self.state == 'registered' \
                and self.product_id.type in ['product', 'consu'] \
                and self.product_uom_qty < self._origin.product_uom_qty:
            # Do not display this warning if the new quantity is below the delivered
            # one; the `write` will raise an `UserError` anyway.
            if self.product_uom_qty < self.qty_delivered:
                return {}
            warning_mess = {
                'title': _('Cantidad pedida disminuida!'),
                'message': _(
                    '¡Estás disminuyendo la cantidad pedida! No olvide actualizar manualmente el pedido de entrega si es necesario.'),
            }
            return {'warning': warning_mess}
        return {}


    def _action_launch_procurement_rule(self):
        """Inicie el método de ejecución del grupo de compras con campos requeridos / personalizados generados por un
         línea de orden de venta. El grupo de compras lanzará '_run_move', '_run_buy' o '_run_manufacture'
         dependiendo de la regla del producto de la línea de orden de venta.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        errors = []
        for line in self:
            if line.state != 'registered' or not line.product_id.type in ('consu', 'product'):
                continue
            qty = 0.0
            for move in line.move_ids.filtered(lambda r: r.state != 'cancel'):
                qty += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom,
                                                          rounding_method='HALF-UP')
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue

            group_id = line.order_id.procurement_group_id
            if not group_id:
                group_id = self.env['procurement.group'].create({
                    'name': line.order_id.name, 'move_type': line.order_id.picking_policy,
                    'octagono_id': line.order_id.id,
                    'partner_id': line.order_id.partner_shipping_id.id,
                })
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.product_uom_qty - qty

            procurement_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            if procurement_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
                product_qty = line.product_uom._compute_quantity(product_qty, quant_uom, rounding_method='HALF-UP')
                procurement_uom = quant_uom

            try:
                self.env['procurement.group'].run(line.product_id, product_qty, procurement_uom,
                                                  line.order_id.partner_shipping_id.property_stock_customer,
                                                  line.name,
                                                  line.order_id.name, values)
            except UserError as error:
                errors.append(error.name)
        if errors:
            raise UserError('\n'.join(errors))
        return True

    def _check_routing(self):
        """ Verify the route of the product based on the warehouse
            return True if the product availibility in stock does not need to be verified,
            which is the case in MTO, Cross-Dock or Drop-Shipping
        """
        is_available = False
        product_routes = self.route_id or (self.product_id.route_ids + self.product_id.categ_id.total_route_ids)

        # Check MTO
        wh_mto_route = self.order_id.warehouse_id.mto_pull_id.route_id
        if wh_mto_route and wh_mto_route <= product_routes:
            is_available = True
        else:
            mto_route = False
            try:
                mto_route = self.env['stock.warehouse']._get_mto_route()
            except UserError:
                # if route MTO not found in ir_model_data, we treat the product as in MTS
                pass
            if mto_route and mto_route in product_routes:
                is_available = True

        # Check Drop-Shipping
        if not is_available:
            for pull_rule in product_routes.mapped('pull_ids'):
                if pull_rule.picking_type_id.sudo().default_location_src_id.usage == 'supplier' and \
                                pull_rule.picking_type_id.sudo().default_location_dest_id.usage == 'customer':
                    is_available = True
                    break

        return is_available

    @api.onchange('product_id')
    def _onchange_product_id_set_lot_domain(self):
        available_lot_ids = []
        if self.order_id.warehouse_id and self.product_id:
            location = self.order_id.warehouse_id.lot_stock_id
            quants = self.env['stock.quant'].read_group([
                ('product_id', '=', self.product_id.id),
                ('location_id', 'child_of', location.id),
                ('quantity', '>', 0),
                ('lot_id', '!=', False),
            ], ['lot_id'], 'lot_id')
            available_lot_ids = [quant['lot_id'][0] for quant in quants]
        self.product_lot_id = False

        is_gps = False
        if self.product_id:
            cat_gps = ['GPS', 'gps', 'Gps']
            if self.product_id.categ_id.name in cat_gps:
                is_gps = True
        return {
            'domain': {'product_lot_id': [('id', 'in', available_lot_ids)]},
            'value': {'is_gps': is_gps},
        }

    def init(self):
        for gps_line in self.env['octagono.gps.line'].search([]):
            is_gps = False
            if gps_line.product_id:
                cat_gps = ['GPS', 'gps', 'Gps']
                if gps_line.product_id.categ_id.name in cat_gps:
                    is_gps = True
            gps_line.write({'is_gps': is_gps})


class OctagonoGPSTags(models.Model):
    _name = 'octagono.gps.tags'
    _description = 'Octagono GPS Tags'

    name = fields.Char(required=True, translate=True)
    color = fields.Integer('Color Index', default=10)

    _sql_constraints = [('name_uniq', 'unique (name)', "Tag name already exists !")]


class OctagonoGPSColors(models.Model):
    _name = 'octagono.gps.colors'
    _description = 'Octagono GPS Colors'
    _order = 'name asc'

    name = fields.Char(required=True, translate=True)
    color = fields.Integer('Color Index', default=10)

    _sql_constraints = [('name_uniq', 'unique (name)', "Tag name already exists !")]

    @api.onchange('name')
    def change_driver(self):
        if self.name:
            self.name = self.name.title()

