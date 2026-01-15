from django.db import models
from django.conf import settings

class Doctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=100)
    experience = models.PositiveIntegerField(help_text="Years of experience" , null=True)
    location = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name} ({self.specialization})"