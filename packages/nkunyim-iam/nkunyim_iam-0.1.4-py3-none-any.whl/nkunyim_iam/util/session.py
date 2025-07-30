from typing import Union
from uuid import uuid4
from django.conf import settings
from django.contrib.messages import get_messages
from django.http import HttpRequest

from nkunyim_iam.util.command import BaseAppCommand



class Session:
    def __init__(self, req: HttpRequest) -> None:
        self.req = req
    
    def get_host_parts(self) -> list[str]:
        host = self.req.get_host()
        host_parts = host.lower().split('.')
        return host_parts
    
    
    def get_subdomain(self) -> str:
        host_parts = self.get_host_parts()
        return host_parts[-3] if len(host_parts) > 2 else "www"
    
    
    def get_domain(self) -> str:
        host_parts = self.get_host_parts()
        return f"{host_parts[-2]}.{host_parts[-1]}"
    
    
    def get_session_key(self) -> str:
        subdomain = self.get_subdomain()
        domain = self.get_domain()
        session_key = f"{subdomain}.{domain}"
        return session_key
    
        
    def set_app(self, app: BaseAppCommand) -> None:
        session_key = f"app.{self.get_session_key()}"
        if app.is_valid:
            data = app.__dict__.copy()
            self.req.session[session_key] = data
            self.req.session.modified = True
        
    
    def get_app(self) -> Union[BaseAppCommand, None]:
        session_key = f"app.{self.get_session_key()}"
        if not bool(session_key in self.req.session):
            return None

        app_sess = self.req.session[session_key]
        app_command = BaseAppCommand(data=app_sess)
        if not app_command.is_valid:
            return None
        
        return app_command
    


class HttpSession(Session):

    def __init__(self, req: HttpRequest) -> None:
        super().__init__(req=req)

        
    def set_account(self, data: dict) -> None:
        session_key = f"http.{self.get_session_key()}"
        self.req.session[session_key] = data
        self.req.session.modified = True


    def get_account(self) -> Union[dict, None]:
        session_key = f"http.{self.get_session_key()}"
        if not bool(session_key in self.req.session):
            return None

        account = self.req.session[session_key]
        return account


    def get_user(self) -> Union[dict, None]:
        user_data = None
        user = self.req.user
        if user.is_authenticated:
            user_data = user.__dict__.copy()
            if not user.is_superuser:
                user_data.pop('is_superuser')
            
        return user_data
    
    
    def get_app_data(self) -> dict:
        app = self.get_app()
        return app.__dict__.copy() if app and app.name else {}
    
    
    def init_menus(self) -> list[dict]:

        xvix_mid = str(uuid4())
        xvix_menus = [{
            "id": str(uuid4()),
            "node": "system", 
            "module": {
                "id": xvix_mid,
                "name": "Xvix",
                "title": "AutoFix",
                "caption": "Manage auto-fix data",
                "icon": "mdi mdi-auto-fix",
                "path": "xvix",
                "route": "#xvix",
            },
            "items": [],
            "is_active": True
        }]

        return xvix_menus
    

    def make_pages(self, menus: list[dict]) -> tuple:

        toolbox_name, manage_name, system_name = "toolbox", "manage", "system"
        toolbox_menus, manage_menus, system_menus = [], [], []

        pages = dict(settings.NKUNYIM_PAGES)

        env = settings.NKUNYIM_ENV

        for menu in menus:
            # Node
            if menu['node'] == toolbox_name:
                toolbox_menus.append(menu)
                
            if menu['node'] == manage_name:
                manage_menus.append(menu)
                
            if menu['node'] == system_name:
                system_menus.append(menu)

            # Menu
            m_name = menu['module']['name']
            m_path = menu['module']['path']
            m_key = "{}Page".format(str(m_name).title())
            m_val = "./{m}/home.{e}".format(m=str(m_path).lower(), e=env)
            pages[m_key] = m_val

            # Item
            if menu['items'] and len(menu['items']) > 0:
                for item in menu['items']:
                    i_name = item['page']['name']
                    i_path = item['page']['path']
                    i_key = "{}{}Page".format(str(m_name).title(), str(i_name).title())
                    i_val = "./{m}/{p}.{e}".format(m=str(m_path).lower(), p=str(i_path).lower(), e=env)
                    pages[i_key] = i_val
        
        navs = []

        if len(toolbox_menus) > 0:
            navs.append(
                {
                    "name": toolbox_name.title(),
                    "menus": toolbox_menus
                }
            )

        if len(manage_menus) > 0:
            navs.append(
                {
                    "name": manage_name.title(),
                    "menus": manage_menus
                }
            )
            
        if len(system_menus) > 0:
            navs.append(
                {
                    "name": system_name.title(),
                    "menus": system_menus
                }
            )

        return navs, pages
    
       
    
    def get_context(self) -> dict:
        path = self.req.path.lower()
        paths = ['/']
        node = "index"

        if len(path) > 1 and path.strip('/') != "":
            paths = path.strip('/').split('/')
            node = paths[-1]

        # Account
        role_data = None
        business_data = None

        menus_data = []

        user_data = self.get_user()
        if user_data and 'username' in user_data:
            
            account = self.get_account()
            if account and 'role' in account:
                menus_data.extend(account['menus'])
                role_data = account['role']
                business_data = account['business']
                
            # Do it last
            if 'is_superuser' in user_data:
                menus_data.extend(self.init_menus())

        navs_data, pages_data = self.make_pages(menus_data)

        # Messaes
        messages = get_messages(request=self.req)
        alert = {}
        alert_map = {
            "debug": "primary",
            "info": "info",
            "success": "success",
            "warning": "warning",
            "error": "danger",
        }
        for message in messages:
            alert["type"] = alert_map[message.tags]
            alert["message"] = str(message)
            
        context_data = self.get_app_data()
        context_data['static'] = settings.STATIC_URL
        context_data['alert'] = alert
        
        
        if self.get_subdomain() == "app":
            context_data['page'] = {
                "path": path,
                "paths": paths,
                "node": node,
                'name': "{}Page".format(node.title()),
                "colour": "nkunyim"
            }
            context_data['pages'] = pages_data
            context_data['navs'] = navs_data
            context_data['role'] = role_data
            context_data['business'] = business_data
            context_data['user'] = user_data
            
        
        if self.get_subdomain() == "api":
            context_data['page'] = {
                "colour": "nkunyim"
            }
            
        return context_data
 

    def kill(self) -> None:
        self.req.session.clear()
        self.req.session.flush()
        

 
class OidcSession(Session):
    
    def __init__(self, req: HttpRequest) -> None:
        super().__init__(req=req)

        
    def set_token(self, data: Union[dict, None]) -> None:
        session_key = f"oidc.{self.get_session_key()}"
        self.req.session[session_key] = data
        self.req.session.modified = True


    def get_token(self) -> Union[dict, None]:
        session_key = f"oidc.{self.get_session_key()}"
        if not bool(session_key in self.req.session):
            return None

        token = self.req.session[session_key]
        return token