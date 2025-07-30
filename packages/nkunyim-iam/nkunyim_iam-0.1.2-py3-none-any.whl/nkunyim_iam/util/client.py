import requests
import base64
import json
from django.conf import settings
from django.http import HttpRequest

from nkunyim_iam.util.command import BaseAppCommand
from nkunyim_iam.util.encryption import Encryption
from  nkunyim_iam.util.session import HttpSession, OidcSession


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
    
    

class OidcClient:
    
    def __init__(self, req: HttpRequest, app: BaseAppCommand) -> None:

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        try:
            base_url = f"https://iam.{app.domain}"
            sess = OidcSession(req=req)
            
            token_data = sess.get_token()
            if token_data and 'access_token' in token_data:
                headers['Authorization'] = f"JWT {token_data['access_token']}"
                
        except Exception as ex:
            raise Exception(f"Exception error occured when initializing the HttpClient. Error detail: {str(ex)}")
        
        self.base_url = base_url
        self.headers = headers
        self.redirect_uri = f"https://app.{app.domain}/auth/login/"

        
        # OIDC URLS
        self.authorization_url = f"{base_url}/authorize?response_type={app.response_type}&client_id={app.client_id}&redirect_uri={self.redirect_uri}"
        self.token_url = f"{base_url}/token"
        self.userinfo_url = f"{base_url}/userinfo"
        self.logout_url = f"{base_url}/logout?client_id={app.client_id}&post_logout_redirect_uri={self.redirect_uri}"
        self.end_session_url = f"{base_url}/end_session?client_id={app.client_id}&post_logout_redirect_uri={self.redirect_uri}"
        
        self.client_id = app.client_id
        self.client_secret = app.client_secret
        self.grant_type = app.grant_type
        

    def get_user_info(self):
        return requests.get(self.userinfo_url, headers=self.headers)
    
    
    def exchange_code_for_token(self, code):
        data = {
            'grant_type': self.grant_type,
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        return requests.post(self.token_url, data=data, headers=self.headers)
        
        
    def logout(self):
        return requests.get(self.logout_url, headers=self.headers)
        
        
    def end_session(self):
        return requests.get(self.end_session_url, headers=self.headers)