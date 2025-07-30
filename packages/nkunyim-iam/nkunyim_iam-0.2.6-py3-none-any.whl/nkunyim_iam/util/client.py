import requests
import base64
import json
from django.conf import settings
from django.http import HttpRequest

from nkunyim_iam.util.encryption import Encryption
from  nkunyim_iam.util.session import HttpSession


class HttpClient:

    def __init__(self, req: HttpRequest, name:str) -> None:
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        try:
            base_url = settings.NKUNYIM_SERVICES[name.upper()]
            sess = HttpSession(req=req)
            
            user_data = sess.get_user()
            if user_data and 'id' in user_data:
                
                plain_text = json.dumps(user_data)
                
                encryption = Encryption()
                cipher_text = encryption.rsa_encrypt(plain_text=plain_text, name=name)
                
                access_token = base64.b64encode(cipher_text)
                headers['Authorization'] = f"JWT {access_token}"
                
        except KeyError as e:
            raise Exception(f"The service configuration variable {name.upper()} has not defined. Error detail: {str(e)}")

        except Exception as ex:
            raise Exception(f"Exception error occured when initializing the HttpClient. Error detail: {str(ex)}")
        
        self.base_url = base_url
        self.headers = headers


    def post(self, path: str, data: dict) -> requests.Response:
        url = self.base_url + path
        return requests.post(url=url, data=data, headers=self.headers)


    def get(self, path: str) -> requests.Response:
        url = self.base_url + path
        return requests.get(url=url, headers=self.headers)


    def put(self, path: str, data: dict) -> requests.Response:
        url = self.base_url + path
        return requests.put(url=url, data=data, headers=self.headers)


    def delete(self, path: str) -> requests.Response:
        url = self.base_url + path
        return requests.delete(url=url, headers=self.headers)
    
    
    def patch(self, path: str, data: dict) -> requests.Response:
        url = self.base_url + path
        return requests.patch(url=url, data=data, headers=self.headers) 
    
    
    def head(self, path: str) -> requests.Response:
        url = self.base_url + path
        return requests.head(url=url, headers=self.headers) 
    
    
    def options(self, path: str) -> requests.Response:
        url = self.base_url + path
        return requests.options(url=url, headers=self.headers)
    
    
    def get_base_url(self) -> str:
        return self.base_url
    
    
    def get_headers(self) -> dict:
        return self.headers 
     
     
    def get_full_url(self, path: str) -> str:
        return self.base_url + path