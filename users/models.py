from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_patient = models.BooleanField(default=True)
    is_doctor = models.BooleanField(default=False)