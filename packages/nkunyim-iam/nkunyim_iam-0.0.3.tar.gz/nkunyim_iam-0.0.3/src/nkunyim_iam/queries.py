from typing import Type
from rest_framework.serializers import ModelSerializer

from nkunyim_util import Query

from .models import User



class UserQuery(Query):
    
    def __init__(self, serializer: Type[ModelSerializer], query_params: dict = None):
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
        