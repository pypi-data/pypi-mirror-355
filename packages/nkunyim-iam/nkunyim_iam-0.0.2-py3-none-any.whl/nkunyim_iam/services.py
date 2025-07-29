from typing import Union

from rest_framework import serializers

from .models import User
from .commands import UserCommand
from .queries import UserQuery



class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        exclude = ['password',]


class UserService:

    def login(self, data: dict) -> Union[User, None]:
        command = UserCommand(data=data, serializer=UserSerializer)
        if not command.is_valid:
            return None
        
        query = UserQuery(serializer=UserSerializer, query_params=data)
        result = query.first()
        if result.data is None:
            command.create()
            data = command.data
        else:
            data = result.data
            if 'is_deleted' in data and data['is_deleted']:
                command.restore(pk=command.id)
                data = command.data
        
        return User(**data)
