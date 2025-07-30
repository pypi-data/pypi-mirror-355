from django.contrib.gis.geoip2 import GeoIP2
from django.http import HttpRequest



class Location:
    
    @staticmethod
    def ip_address(req: HttpRequest) -> str:
        x_forwarded_for = req.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = req.META.get('REMOTE_ADDR')
            
        return str(ip)
    
    
    @staticmethod
    def geo_data(req: HttpRequest) -> dict:
        
        #User Agent
        user_agent = req.META['HTTP_USER_AGENT']

        if 'User-Agent' in req.headers:
            user_agent = req.headers['User-Agent']

        if 'user-agent' in req.headers:
            user_agent = req.headers['user-agent']

        # IP Address
        user_ip = Location.ip_address(req)
        if user_ip.startswith("192.168.") or user_ip.endswith(".0.0.1"):
            user_ip = "154.160.22.132"

        g = GeoIP2()
        city = g.city(user_ip)

        return {
            "user_ip": user_ip,
            "user_agent": user_agent,
            "city": city['city'],
            "continent_code": city['continent_code'],
            "continent_name": city['continent_name'],
            "country_code": city['country_code'],
            "country_name": city['country_name'],
            "is_in_eu": city['is_in_european_union'],
            "latitude": city['latitude'],
            "longitude": city['longitude'],
            "postal_code": city['postal_code'],
            "region": city['region'],
            "time_zone": city['time_zone'],
        }