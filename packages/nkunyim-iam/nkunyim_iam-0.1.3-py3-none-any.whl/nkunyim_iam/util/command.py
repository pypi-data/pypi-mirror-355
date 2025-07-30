from typing import Type, Union
from uuid import UUID
from rest_framework.serializers import ModelSerializer

from nkunyim_iam.util.validation import Validation, VAL



class Command(Validation):
    
    def __init__(self):
        super().__init__()
        self.queryset = None
        

    def get(self, serializer: Type[ModelSerializer]) -> Union[dict[str, VAL], None]:
        result = serializer(self.queryset, many=False)
        return result.data




class BaseAppCommand(Command):
    
    def __init__(self, data: dict) -> None:
        schema = {
            'secret': {
                'typ': 'str',
            },
            'domain': {
                'typ': 'str',
            },
            'scope': {
                'typ': 'str',
            },
            'name': {
                'typ': 'str',
            },
            'title': {
                'typ': 'str',
            },
            'caption': {
                'typ': 'str',
            }
        }
        
        self.check(schema=schema, data=data)
        
        self.id = UUID(data['id']) if 'id' in data else None
        self.client_id = data['client_id']
        self.client_secret = data['client_secret']
        self.response_type = data['response_type'] if 'response_type' in data else 'code'
        self.grant_type = data['grant_type'] if 'grant_type' in data else 'authorization_code'
        self.domain = data['domain']
        self.scope = data['scope'] if 'scope' in data else 'openid profile email phone'
        self.name = data['name']
        self.title = data['title']
        self.caption = data['caption']
        self.description = data['description'] if 'description' in data else None
        self.keywords = data['keywords'] if 'keywords' in data else None
        self.image_url = data['image_url'] if 'image_url' in data else None
        self.logo_url = data['logo_url'] if 'logo_url' in data else None
        self.icon_url = data['icon_url'] if 'icon_url' in data else None
        self.tags = data['tags'] if 'tags' in data else None
        self.is_active = bool(data['is_active']) if 'is_active' in data else False