from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    # username & email already exist in AbstractUser
    full_name = models.CharField(max_length=100, blank=False)
    shipping_address = models.TextField(blank=False)
    email = models.EmailField(unique=True, blank=False, null=False)

    def __str__(self):
        return self.username