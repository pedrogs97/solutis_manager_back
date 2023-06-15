"""
Authenticate models
"""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import check_password
from django.db import models

from utils.base.mixins import BasePermissionsMixin
from utils.base.models import BaseModel
from utils.images import OverwriteImage, upload_to


class User(AbstractBaseUser, BaseModel, BasePermissionsMixin):
    """
    User model
    """

    full_name = models.CharField(max_length=255)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    taxpayer_identification = models.CharField(max_length=13, unique=True)
    image = models.ImageField(
        blank=True,
        null=True,
        storage=OverwriteImage(),
        upload_to=upload_to,
        max_length=255,
    )
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = "email"

    objects = BaseUserManager()

    class Meta:
        """
        User Class Meta
        """

        db_table = "user"
        verbose_name = "user"
        verbose_name_plural = "users"

    def check_password(self, raw_password) -> bool:
        """
        Return a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes. Update password
        """
        return check_password(raw_password, self.password)
