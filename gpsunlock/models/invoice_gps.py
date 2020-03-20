
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero
import time
from datetime import datetime

class CustomInvoiceOctagonoGps(models.Model):
    _inherit = 'account.invoice'

    prueba_fecha = fields.Datetime(string="Fechas prueba")

    @api.onchange("partner_id")
    def onchange_partner(self):
        invoice_line = []
        account = self.env['account.account'].search([('code','=', '41010100'),('company_id','=',self.env['res.company']._company_default_get('account.invoice').id)])
        monthly_vehicle = self.env['octagono.gps'].search([('partner_id','=', self.partner_id.id),('state','!=','cancel'),('select_period','=','monthly')])
        annual_vehicle = self.env['octagono.gps'].search([('partner_id','=', self.partner_id.id),('state','!=','cancel'),('select_period','=','annual')])
        monthly_description = 'GPS Renovacion Mensual \n'
        annual_description = 'GPS Renovacion Anual \n'
        new_year_vehicle = []
        # actual_month = datetime.now().month
        # actual_year = datetime.now().year

        if self.partner_id and self.prueba_fecha:

            actual_month = int(self.prueba_fecha.split('-')[1])
            actual_year = int(self.prueba_fecha.split('-')[0])
            if monthly_vehicle:
                monthly_price= self.partner_id.monthly_price
                if self.partner_id.early_discount_payment:
                    monthly_price = monthly_price - (monthly_price*10/100)
                for vehicle in monthly_vehicle:
                    monthly_description = monthly_description + vehicle.model_id.brand_id.name + '   ' + vehicle.model_id.name + '   '+ (vehicle.color.name or '') + '   ' + vehicle.model_year + '    ' + vehicle.license_plate + '    ' + (vehicle.driver or '') + ' ' + (vehicle.install_date.split(' ')[0] or '') +'\n'
                invoice_line.append((0, 0, {'product_id': 5,'name': monthly_description,'quantity': len(monthly_vehicle),'account_id': account.id, 'price_unit': monthly_price}))
            if annual_vehicle:
                print(annual_vehicle)
                for vehicle in annual_vehicle:
                    vehicle_installation_month = int(vehicle.install_date.split('-')[1])
                    vehicle_installation_year = int(vehicle.install_date.split('-')[0])
                    if vehicle_installation_month == actual_month and vehicle_installation_year != actual_year:
                        new_year_vehicle.append(vehicle)
                if new_year_vehicle:
                    annual_price =  self.partner_id.annual_price
                    if self.partner_id.early_discount_payment:
                        annual_price = annual_price - (annual_price * 10 / 100)

                    for vehicle in new_year_vehicle:
                        annual_description = annual_description + vehicle.model_id.brand_id.name + '   ' + vehicle.model_id.name + '   ' + (vehicle.color.name or '') + '   ' + vehicle.model_year + '    ' + vehicle.license_plate + '    ' + (vehicle.driver or '') + ' ' + (vehicle.install_date.split(' ')[0] or '') + '\n'
                    invoice_line.append((0, 0, {'product_id': 10, 'name': annual_description, 'quantity': len(new_year_vehicle),'account_id': account.id, 'price_unit': annual_price}))

            self.invoice_line_ids = invoice_line
