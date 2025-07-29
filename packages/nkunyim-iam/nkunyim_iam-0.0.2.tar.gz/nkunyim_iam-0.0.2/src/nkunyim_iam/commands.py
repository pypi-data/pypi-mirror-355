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
        self.phone_number = data['phone_number']
        self.email_address = data['email_address']
        self.full_name = data['full_name'] if 'full_name' in data else None
        self.photo_url = data['photo_url'] if 'photo_url' in data else None


    def create(self) -> Self:
        queryset = User.objects.create(
            id=self.id,
            username=self.username,
            nickname=self.nickname,
            phone_number=self.phone_number,
            email_address=self.email_address
        )

        password = str(uuid4())
        queryset.set_password(password)
        
        if self.full_name:
            queryset.full_name = self.full_name
            
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
            queryset.phone_number = self.phone_number
            queryset.email_address = self.email_address
            queryset.is_deleted = False
            queryset.is_active = True
            queryset.deleted_at = None
            
            if self.full_name:
                queryset.full_name = self.full_name
                
            if self.photo_url:
                queryset.photo_url = self.photo_url
                
            password = str(uuid4())
            queryset.set_password(password)
            
            queryset.save()

        self.queryset = queryset
        return self.get()
    

    def delete(self, pk: UUID, archive: bool = True) -> Self:
        if archive:
            queryset = User.objects.get(pk=pk)
            queryset.is_deleted = True
            queryset.deleted_at = datetime.now()
            queryset.save()
        else:
            User.objects.get(pk=pk).delete()

        self.queryset = User.objects.filter(id=pk, is_deleted=False).first()
        return self.get()


    def restore(self, pk: UUID) -> Self:
        queryset = User.objects.get(pk=pk)
        
        queryset.is_deleted = False
        queryset.deleted_at = None
        queryset.save()
 
        self.queryset = queryset
        return self.get()