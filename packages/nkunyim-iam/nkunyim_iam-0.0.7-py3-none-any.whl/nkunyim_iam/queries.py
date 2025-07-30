from typing import Type, Union
from rest_framework.serializers import ModelSerializer

from .models import User
from .util import Query



class UserQuery(Query):
    
    def __init__(self, serializer: Type[ModelSerializer], query_params: Union[dict, None] = None):
        super().__init__(serializer=serializer, model=User)
        
        self.path = 'api/users/'
        schema = {
            'id': 'uuid',
            'username': 'str',
            'phone_number': 'str',
            'email_address': 'str',
            'is_active': 'bool',
        }
        
        self.extract(schema=schema, query_params=query_params)
        