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
        command = UserCommand(data=data)
        if not command.is_valid:
            return None
        
        query = UserQuery(serializer=UserSerializer, query_params=data)
        user_data = query.one(pk=command.id)

        if not user_data:
            user_data = command.create()
        else:
            user_data = command.update(pk=command.id)
            
        return user_data
