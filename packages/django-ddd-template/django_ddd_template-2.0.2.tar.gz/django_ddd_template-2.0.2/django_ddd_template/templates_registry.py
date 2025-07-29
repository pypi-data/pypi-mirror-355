from textwrap import dedent

TEMPLATES = {
    "domain/entities/{app_name}.py": dedent('''
        class {{AppName}}:
            def __init__(self, id, name, description):
                self.id = id
                self.name = name
                self.description = description
    ''').strip(),

    "domain/repositories/{app_name}_repository.py": dedent('''
from abc import ABC, abstractmethod

class {{AppName}}Repository(ABC):
    @abstractmethod
    def get_by_id(self, entity_id): pass

    @abstractmethod
    def save(self, entity): pass
''').strip(),

    "domain/services/{app_name}_service.py": dedent('''
from {{app_name}}.domain.entities.{{app_name}} import {{AppName}}

class {{AppName}}Service:
    def __init__(self, repository):
        self.repository = repository

    def register_entity(self, name, description):
        entity = {{AppName}}(None, name, description)
        return self.repository.save(entity)
''').strip(),

    "infrastructure/models/{app_name}_model.py": dedent('''
from django.db import models

class {{AppName}}Model(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
''').strip(),

    "infrastructure/repositories/{app_name}_repository.py": dedent('''
from {{app_name}}.domain.entities.{{app_name}} import {{AppName}}
from {{app_name}}.domain.repositories.{{app_name}}_repository import {{AppName}}Repository
from {{app_name}}.infrastructure.models.{{app_name}}_model import {{AppName}}Model

class {{AppName}}Repository({{AppName}}Repository):
    def get_by_id(self, entity_id):
        model = {{AppName}}Model.objects.get(id=entity_id)
        return {{AppName}}(model.id, model.name, model.description)

    def save(self, entity):
        model = {{AppName}}Model(name=entity.name, description=entity.description)
        model.save()
        entity.id = model.id
        return entity
''').strip(),

    "infrastructure/serializers/{app_name}_serializer.py": dedent('''
from rest_framework import serializers
from {{app_name}}.infrastructure.models.{{app_name}}_model import {{AppName}}Model

class {{AppName}}Serializer(serializers.ModelSerializer):
    class Meta:
        model = {{AppName}}Model
        fields = ['id', 'name', 'description']
''').strip(),

    "infrastructure/views/{app_name}_view.py": dedent('''
from rest_framework import viewsets
from {{app_name}}.infrastructure.models.{{app_name}}_model import {{AppName}}Model
from {{app_name}}.infrastructure.serializers.{{app_name}}_serializer import {{AppName}}Serializer

class {{AppName}}ViewSet(viewsets.ModelViewSet):
    queryset = {{AppName}}Model.objects.all()
    serializer_class = {{AppName}}Serializer
''').strip(),

    "infrastructure/urls.py": dedent('''
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from {{app_name}}.infrastructure.views.{{app_name}}_view import {{AppName}}ViewSet

router = DefaultRouter()
router.register(r'$base_url', {{AppName}}ViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
''').strip(),

    "tests/test_{app_name}_service.py": dedent('''
import unittest
from {{app_name}}.domain.services.{{app_name}}_service import {{AppName}}Service
from {{app_name}}.domain.entities.{{app_name}} import {{AppName}}

class InMemory{{AppName}}Repository:
    def __init__(self):
        self.data = {}
        self._id_counter = 1

    def get_by_id(self, entity_id):
        return self.data.get(entity_id)

    def save(self, entity):
        entity.id = self._id_counter
        self.data[self._id_counter] = entity
        self._id_counter += 1
        return entity

class {{AppName}}ServiceTestCase(unittest.TestCase):
    def test_register_entity(self):
        repo = InMemory{{AppName}}Repository()
        service = {{AppName}}Service(repo)

        entity = service.register_entity("Example", 'description')

        self.assertIsNotNone(entity.id)
        self.assertEqual(entity.name, "Example")
        self.assertEqual(entity.description, 'description')

if __name__ == '__main__':
    unittest.main()
''').strip(),
}
