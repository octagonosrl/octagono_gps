# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    octagono_note = fields.Text(string='Default Terms and Conditions the octagono', translate=True)
