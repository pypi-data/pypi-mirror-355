import copy
from django.contrib.gis.geoip2 import GeoIP2
from django.http import HttpRequest



class Location:
    
    def __init__(self, req: HttpRequest) -> None:
        self.req = req
        
    
    def get_ip_address(self) -> str:
        x_forwarded_for = str(self.req.META.get('HTTP_X_FORWARDED_FOR'))
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        elif self.req.META.get('HTTP_X_REAL_IP'):
            ip = self.req.META.get('HTTP_X_REAL_IP')
        else:
            ip = self.req.META.get('REMOTE_ADDR')
            
        return str(ip)
    
    
    def get_geo_data(self) -> dict:
        
        # django.contrib.gis.geoip2.GeoIP2 is used to get the geo data
        # from the IP address of the user.
        # https://docs.djangoproject.com/en/5.2/ref/contrib/gis/geoip2/
        
        #User Agent
        user_agent = self.req.META['HTTP_USER_AGENT']

        if 'User-Agent' in self.req.headers:
            user_agent = self.req.headers['User-Agent']

        if 'user-agent' in self.req.headers:
            user_agent = self.req.headers['user-agent']

             
        # IP Address
        user_ip = self.get_ip_address()
        if user_ip.startswith("192.168.") or user_ip.endswith(".0.0.1"):
            user_ip = "154.160.22.132"

        g = GeoIP2()
        data = copy.deepcopy(g.city(user_ip))
        
        data['user_ip'] = user_ip
        data['user_agent'] = self.req.user_agent.__dict__ if hasattr(self.req, 'user_agent') else user_agent
        
        return data
