
# 🧠 Arquitectura Basada en DDD para Django Rest Framework


## 🚀 Instalación

Puedes instalarlo directamente desde PyPI:

```
pip install django-ddd-template
```

## 🚀 Después de instalar el paquete, puedes usar el siguiente comando para generar una app con estructura DDD:


```
django-ddd startapp <nombre_de_la_app>
```


---

## 📦 Estructura General
Esta estructura está basada en los principios de Domain-Driven Design (DDD) aplicada con Django + Django Rest Framework.

```

entity_app/
├── domain/
│   ├── entities/           # Entidades del dominio
│   ├── events/             # Eventos de dominio
│   ├── repositories/       # Interfaces de repositorios
│   └── services/           # Lógica de negocio
├── infrastructure/
│   ├── models/             # Modelos ORM
│   ├── repositories/       # Repositorios concretos
│   ├── serializers/        # Serializadores DRF
│   ├── views/              # Vistas DRF
│   └── urls.py             # Enrutamiento de la app
├── migrations/             # Migraciones Django
├── apps.py                 # Configuración de la app
├── models.py               # Opcional si se usa infraestructura/models
└── tests/                  # Pruebas unitarias
```

---

## 🧱 Ejemplo de Implementación

### Dominio

#### Entidad

```python
# domain/entities/entity.py
class Entity:
    def __init__(self, id, name, value):
        self.id = id
        self.name = name
        self.value = value
```

#### Repositorio (interfaz)

```python
# domain/repositories/entity_repository.py
from abc import ABC, abstractmethod

class EntityRepository(ABC):
    @abstractmethod
    def get_by_id(self, entity_id): pass

    @abstractmethod
    def save(self, entity): pass
```

#### Servicio

```python
# domain/services/entity_service.py
from entity_app.domain.entities.entity import Entity

class EntityService:
    def __init__(self, repository):
        self.repository = repository

    def register_entity(self, name, value):
        entity = Entity(None, name, value)
        return self.repository.save(entity)
```

---

### Infraestructura

#### Modelo

```python
# infrastructure/models/entity_model.py
from django.db import models

class EntityModel(models.Model):
    name = models.CharField(max_length=255)
    value = models.IntegerField()
```

#### Repositorio (implementación)

```python
# infrastructure/repositories/django_entity_repository.py
from entity_app.domain.entities.entity import Entity
from entity_app.domain.repositories.entity_repository import EntityRepository
from entity_app.infrastructure.models.entity_model import EntityModel

class DjangoEntityRepository(EntityRepository):
    def get_by_id(self, entity_id):
        model = EntityModel.objects.get(id=entity_id)
        return Entity(model.id, model.name, model.value)

    def save(self, entity):
        model = EntityModel(name=entity.name, value=entity.value)
        model.save()
        entity.id = model.id
        return entity
```

#### Serializador

```python
# infrastructure/serializers/entity_serializer.py
from rest_framework import serializers
from entity_app.infrastructure.models.entity_model import EntityModel

class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityModel
        fields = ['id', 'name', 'value']
```

#### Vista

```python
# infrastructure/views/entity_view.py
from rest_framework import viewsets
from entity_app.infrastructure.models.entity_model import EntityModel
from entity_app.infrastructure.serializers.entity_serializer import EntitySerializer

class EntityViewSet(viewsets.ModelViewSet):
    queryset = EntityModel.objects.all()
    serializer_class = EntitySerializer
```

#### URLs

```python
# infrastructure/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from entity_app.infrastructure.views.entity_view import EntityViewSet

router = DefaultRouter()
router.register(r'entities', EntityViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

---

### ✅ Pruebas

```python
# tests/test_entity_service.py
import unittest
from entity_app.domain.services.entity_service import EntityService
from entity_app.domain.entities.entity import Entity

class InMemoryEntityRepository:
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

class EntityServiceTestCase(unittest.TestCase):
    def test_register_entity(self):
        repo = InMemoryEntityRepository()
        service = EntityService(repo)

        entity = service.register_entity("Example", 100)

        self.assertIsNotNone(entity.id)
        self.assertEqual(entity.name, "Example")
        self.assertEqual(entity.value, 100)

if __name__ == '__main__':
    unittest.main()
```

---

## ▶️ Ejecución de Pruebas

```bash
python manage.py test entity_app.tests.test_entity_service
```

---

## 📌 Notas

- Se recomienda inyectar las dependencias (repositorios) desde vistas o gestores.
- Puedes extender `services` con lógica más compleja según tus reglas de negocio.
