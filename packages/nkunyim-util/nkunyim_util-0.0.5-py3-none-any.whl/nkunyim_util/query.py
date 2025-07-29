from typing import Self, Type
from uuid import UUID

from django.db import models
from rest_framework.serializers import ModelSerializer

from nkunyim_util import Pagination


class Query(Pagination):

    def __init__(self, model: Type[models.Model], serializer:  Type[ModelSerializer]):
        super().__init__(serializer=serializer)

        self.model = model

    def one(self, pk: UUID) -> Self:
        self.queryset = self.model.objects.get(pk=pk)
        return self.get()

    def first(self) -> Self:
        self.queryset = self.model.objects.filter(**self.params).first()
        return self.get()

    def many(self) -> Self:
        if self.params:
            self.queryset = self.model.objects.filter(**self.params)
        else:
            self.queryset = self.model.objects.all()

        return self.list()

    def all(self) -> Self:
        self.queryset = self.model.objects.all()
        return self.list()

