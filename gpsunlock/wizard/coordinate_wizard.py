from odoo import models, fields, api
import urllib.request, json, requests

class coordinate_wizard(models.TransientModel):
    _name = "coordinate.wizard"
    coordinate_image = fields.Binary()
    coordinate_url = fields.Char()

    @api.model
    def default_get(self, fields):
        result = super(coordinate_wizard, self).default_get(fields)
        if self._context.get('active_id'):
            device = self.env['octagono.gps'].browse([self._context.get('active_id')])

            line = device.order_line.filtered(lambda p:'GPS' in p.product_id.name and p.product_id.octagono_ok)

            deviceID = line.product_lot_id.name
            # result['end_date'] = employee_id.contract_id.date_end
            url = "http://192.227.91.57/services/getDevice.php?deviceID=" + str(deviceID)
            response = urllib.request.urlopen(url)
            data = json.loads(response.read().decode("utf-8"))
            print(data['devices'])

            lat = data['devices'][0]['lastValidLatitude']
            lng = data['devices'][0]['lastValidLongitude']
            
            result['coordinate_url'] = self.get_googlemap_url(lat,lng)
            #result['coordinate_image'] = "/gpsunlock/static/image/Dominican-Republic-700x420.jpg"
            
        return result

    def get_googlemap_image(self,lat,lng):
        # Enter your api key here 
        api_key = "AIzaSyD3h_x_PaiMZ6fTrL_fDc5m0Z4VfYf--cQ" # octagono_gps model key (Not restricted)
        # url variable store url 
        url = "https://maps.googleapis.com/maps/api/staticmap?"
        # center defines the center of the map, 
        # equidistant from all edges of the map.  
        center = lat+","+lng
        # zoom defines the zoom 
        # level of the map 
        zoom = 16
        # get method of requests module 
        # return response object 
        r = requests.get(url 
            + "center=" + center 
            + "&zoom=" + str(zoom) 
            + "&size=870x400"
            + "&maptype=roadmap"
            + "&markers=color:red%7Clabel:C%7C" + center
            + "&key=" + api_key 
            #+ "sensor = false"
            + "&visual_refresh=true"
            )
        return r 

    def get_googlemap_url(self,lat,lng):
        # Enter your api key here 
        api_key = "AIzaSyD3h_x_PaiMZ6fTrL_fDc5m0Z4VfYf--cQ" # octagono_gps model key (Not restricted)
        # url variable store url 
        url = "https://maps.googleapis.com/maps/api/staticmap?"
        # center defines the center of the map, 
        # equidistant from all edges of the map.  
        center = lat+","+lng
        # zoom defines the zoom 
        # level of the map 
        zoom = 16
        # get method of requests module 
        # return response object 
        r = url + "center=" + center + "&zoom=" + str(zoom) + "&size=864x540" + "&maptype=roadmap" + "&markers=color:red%7Clabel:C%7C"+ center + "&key=" + api_key + "&visual_refresh=true"
            
        return r 