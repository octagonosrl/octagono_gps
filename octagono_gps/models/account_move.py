from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move"

    account = fields.Char(related="partner_id.Cuenta_GPS", store=True, string="Cuenta")
