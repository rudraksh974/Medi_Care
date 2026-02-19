from django.db import models
from django.conf import settings

class Doctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile')
    SPECIALIZATION_CHOICES = [
        ('General Physician', 'General Physician'),
        ('Cardiologist', 'Cardiologist'),
        ('Dermatologist', 'Dermatologist'),
        ('Neurologist', 'Neurologist'),
        ('Orthopedist', 'Orthopedist'),
        ('Pediatrician', 'Pediatrician'),
        ('Psychiatrist', 'Psychiatrist'),
        ('Gynecologist', 'Gynecologist'),
        ('ENT Specialist', 'ENT Specialist'),
        ('Dentist', 'Dentist'),
        ('Ophthalmologist', 'Ophthalmologist'),
        ('Urologist', 'Urologist'),
        ('Gastroenterologist', 'Gastroenterologist'),
        ('Pulmonologist', 'Pulmonologist'),
        ('Oncologist', 'Oncologist'),
    ]

    specialization = models.CharField(max_length=100, choices=SPECIALIZATION_CHOICES, default='General Physician')
    experience = models.PositiveIntegerField(help_text="Years of experience" , null=True)
    location = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name} ({self.specialization})"
    

class CachedHospital(models.Model):
    name = models.CharField(max_length=200)
    lat = models.FloatField()
    lng = models.FloatField()
    address = models.CharField(max_length=300, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
