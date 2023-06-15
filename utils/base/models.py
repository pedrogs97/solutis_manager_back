"""Project base model"""
import uuid

from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """Base Model for all models"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(db_index=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        """Meta class"""

        abstract = True
