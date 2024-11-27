from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.invoice"

    account = fields.Char(related="partner_id.x_studio_field_ddQ6z", store=True, string="Cuenta")
