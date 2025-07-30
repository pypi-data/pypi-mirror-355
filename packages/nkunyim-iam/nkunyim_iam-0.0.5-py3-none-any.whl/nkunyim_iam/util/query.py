from typing import Type, Union
from uuid import UUID

from django.conf import settings
from django.core.paginator import Paginator
from django.db import models
from rest_framework.serializers import ModelSerializer

from .validation import Validation, VAL


class Query(Validation):

    def __init__(self, model: Type[models.Model], serializer:  Type[ModelSerializer]):

        self.path: Union[str, None] = None
        self.model = model
        self.serializer: Type[ModelSerializer] = serializer
        
        
    def _list(self, queryset):
        
        paginator = Paginator(queryset, int(self.rows))
        queryset = paginator.page(int(self.page))
        
        query_params = ""
        if self.params:
            for key in dict(self.params).keys():
                query_params += f"&{key}={self.params[key]}"
                
        _next = f"{settings.APP_BASE_URL}/{self.path}?rows={self.rows}&page={self.page + 1}{query_params}" if queryset.has_next() else None
        _prev = f"{settings.APP_BASE_URL}/{self.path}?rows={self.rows}&page={self.page - 1}{query_params}" if queryset.has_previous() else None
        
        result = self.serializer(queryset, many=True)
        return {
            'count': paginator.count,
            'next': _next,
            'prev': _prev,
            'data': result.data
        }


    def one(self, pk: UUID) -> Union[dict[str, VAL], None]:
        queryset = self.model.objects.get(pk=pk)
        result = self.serializer(queryset, many=False)
        return result.data
    

    def first(self) -> Union[dict[str, VAL], None]:
        if not self.params:
            return None
        
        queryset = self.model.objects.filter(**self.params).first()
        result = self.serializer(queryset, many=False)
        return result.data


    def many(self) -> dict:
        if self.params:
            queryset = self.model.objects.filter(**self.params)
        else:
            queryset = self.model.objects.all()

        return self._list(queryset=queryset)


    def all(self) -> dict:
        queryset = self.model.objects.all()
        return self._list(queryset=queryset)

