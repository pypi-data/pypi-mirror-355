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
        data = query.one(pk=command.id).data

        if not data:
            command.create()
            data = command.data
        else:
            command.update(pk=command.id)
            
        return User(**data)
