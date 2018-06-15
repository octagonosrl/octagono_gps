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
    image = fields.Binary(related='brand_id.image', string="Logo")
    image_medium = fields.Binary(related='brand_id.image_medium', string="Logo (medium)")
    image_small = fields.Binary(related='brand_id.image_small', string="Logo (small)")

    @api.multi
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
            if record.name:
                record.name = record.name.title()

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].title()
        return super(OctagonoModel, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].title()
        return super(OctagonoModel, self).write(vals)


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
    image_medium = fields.Binary(
        string="Medium-sized image",
        attachment=True,
        help="Medium-sized logo of the brand. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved. "
             "Use this field in form views or some kanban views.")
    image_small = fields.Binary(
        string="Small-sized image",
        attachment=True,
        help="Small-sized logo of the brand. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")

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

    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        if vals.get('name'):
            vals['name'] = vals['name'].title()
        return super(OctagonoModelBrand, self).write(vals)
