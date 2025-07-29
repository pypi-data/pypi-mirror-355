from datetime import datetime
from typing import Self, Type
from uuid import UUID, uuid4

from rest_framework.serializers import ModelSerializer

from nkunyim_util import Validation

from nkunyim_iam.models import User


class UserCommand(Validation):
    
    def __init__(self, data: dict, serializer: Type[ModelSerializer]):
        super().__init__(serializer=serializer)
        
        
        schema = {
            'id': {
                'typ': 'uuid',
            },
            'username': {
                'typ': 'str',
            },
            'nickname': {
                'typ': 'str',
            },
            'first_name': {
                'typ': 'str',
            },
            'last_name': {
                'typ': 'str',
            },
            'phone_number': {
                'typ': 'str',
            },
            'email_address': {
                'typ': 'str',
            }
        }
        
        self.check(schema=schema, data=data)
        
        self.id = UUID(data['id'])
        self.username = data['username']
        self.nickname = data['nickname']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.phone_number = data['phone_number']
        self.email_address = data['email_address']
        self.photo_url = data['photo_url'] if 'photo_url' in data else None
        self.is_admin = bool(data['is_admin']) if 'is_admin' in data else False
        self.is_superuser = bool(data['is_superuser']) if 'is_superuser' in data else False
        self.is_verified = bool(data['is_verified']) if 'is_verified' in data else False
        self.is_active = bool(data['is_active']) if 'is_active' in data else True


    def create(self) -> Self:
        queryset = User.objects.create(
            id=self.id,
            username=self.username,
            nickname=self.nickname,
            first_name=self.first_name,
            last_name=self.last_name,
            phone_number=self.phone_number,
            email_address=self.email_address,
            is_admin=self.is_admin,
            is_superuser=self.is_superuser,
            is_verified=self.is_verified,
            is_active=self.is_active,
        )

        password = str(uuid4())
        queryset.set_password(password)
        
        if self.photo_url:
            queryset.photo_url = self.photo_url
            
        queryset.save()
            
        self.queryset = queryset
        return self.get()


    def update(self, pk: UUID) -> Self:
        queryset = User.objects.get(pk=pk)

        if queryset:
            queryset.username = self.username
            queryset.nickname = self.nickname
            queryset.first_name = self.first_name
            queryset.last_name = self.last_name
            queryset.phone_number = self.phone_number
            queryset.email_address = self.email_address
            queryset.is_verified = self.is_verified
            queryset.is_active = self.is_active
            queryset.is_admin = self.is_admin
            queryset.is_superuser = self.is_superuser
            
            if self.photo_url:
                queryset.photo_url = self.photo_url
                
            password = str(uuid4())
            queryset.set_password(password)
            
            queryset.save()

        self.queryset = queryset
        return self.get()


    def delete(self, pk: UUID) -> Self:
        queryset = User.objects.get(pk=pk)
        queryset.delete()

        self.queryset = queryset
        return self.get()
