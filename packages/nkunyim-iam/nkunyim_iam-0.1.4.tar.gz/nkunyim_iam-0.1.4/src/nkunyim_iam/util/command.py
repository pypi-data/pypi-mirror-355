from datetime import datetime
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
        self.client_id = str(data['client_id'])
        self.client_secret = str(data['client_secret'])
        self.response_type = str(data['response_type']) if 'response_type' in data else 'code'
        self.grant_type = str(data['grant_type']) if 'grant_type' in data else 'authorization_code'
        self.domain = str(data['domain'])
        self.scope = str(data['scope']) if 'scope' in data else 'openid profile email phone'
        self.name = str(data['name'])
        self.title = str(data['title'])
        self.caption = str(data['caption'])
        self.description = str(data['description']) if 'description' in data else None
        self.keywords = str(data['keywords']) if 'keywords' in data else None
        self.image_url = str(data['image_url']) if 'image_url' in data else None
        self.logo_url = str(data['logo_url']) if 'logo_url' in data else None
        self.icon_url = str(data['icon_url']) if 'icon_url' in data else None
        self.colour = str(data['colour']) if 'colour' in data else 'nkunyim'
        self.tags = str(data['tags']) if 'tags' in data else None
        self.is_active = bool(data['is_active']) if 'is_active' in data else True
        self.created_at = datetime.strptime(str(data['created_at']), '%Y-%m-%d %H:%M:%S') if 'created_at' in data else None
        self.updated_at = datetime.strptime(str(data['updated_at']), '%Y-%m-%d %H:%M:%S') if 'updated_at' in data else None