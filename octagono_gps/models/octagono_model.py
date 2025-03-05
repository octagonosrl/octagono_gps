# -*- coding: utf-8 -*-
# pylint: disable=C0111, R0903
import logging

from odoo import models, fields, api, tools  # pylint: disable=E0401

_logger = logging.getLogger(__name__)


class OctagonoModel(models.Model):
    _name = 'octagono.model'
    _description = 'Model of a vehicle'
    _order = 'name asc'

    name = fields.Char(string='Model name', required=True)
    brand_id = fields.Many2one(comodel_name='octagono.model.brand',
                               string='Make',
                               required=True,
                               help='Make of the vehicle')
    image = fields.Binary(related='brand_id.image', string="Logo", store=True)

    _sql_constraints = [('name_uniq', 'unique (name)', "Nombre del modelo ya existe !")]


    @api.depends('name', 'brand_id')
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            if record.brand_id.name:
                name = record.brand_id.name + '/' + name
            res.append((record.id, name))
        return res

    @api.onchange('brand_id')
    def _onchange_brand(self):
        if self.brand_id:
            self.image_medium = self.brand_id.image
        else:
            self.image_medium = False

    @api.onchange('name')
    def change_name(self):
        for record in self:
            # self.id
            if record.name:
                if self._origin:
                    ## record.name = record.name
                    # Obteniendo el id del modelo editado
                    id = self._origin.id
                    if id:
                        # nuevo nombre del modelo
                        model_name = record.name
                        # Actualizando el nombre del modelo
                        sql_upd_modelo = "update octagono_model set name='" + model_name + "' where id = " + str(id) + ";"
                        self.env.cr.execute(sql_upd_modelo)
                        # Buscando los vehiculos relacionados al modelo modificado
                        sql = "select id, name, model_id from octagono_gps where model_id = " + str(id) + ";"
                        self.env.cr.execute(sql)
                        res_all = self.env.cr.fetchall()
                        for v in res_all:
                            # Creando el nuevo nombre del vehiculo
                            veh_id = v[0]
                            veh_name = (v[1]).split("/")
                            new_veh_name = veh_name[0] + "/" + model_name + "/" + veh_name[2]
                            # actualizando el nombre del vehiculo
                            sql_update = "update octagono_gps set name = '" + new_veh_name + "' where id = " + str(veh_id) + ";"
                            self.env.cr.execute(sql_update)
                            logging.info(sql_update)

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].title()
        return super().create(vals)


    def write(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].title()
        return super().write(vals)


class OctagonoModelBrand(models.Model):
    _name = 'octagono.model.brand'
    _description = 'Brand of the vehicle'
    _order = 'name asc'

    name = fields.Char('Make', required=True)
    image = fields.Binary(
        string="Logo",
        attachment=True,
        help="This field holds the image used as logo for the brand, "
             "limited to 1024x1024px.")

    _sql_constraints = [('name_uniq', 'unique (name)', "Nombre de la marca ya existe !")]

    @api.onchange('name')
    def change_name(self):
        for record in self:
            if record.name:
                record.name = record.name.title()

    @api.model
    def create(self, vals):
        tools.image_resize_images(vals)
        if vals.get('name'):
            vals['name'] = vals['name'].title()
        return super(OctagonoModelBrand, self).create(vals)


    def write(self, vals):
        tools.image_resize_images(vals)
        if vals.get('name'):
            vals['name'] = vals['name'].title()
        return super(OctagonoModelBrand, self).write(vals)
