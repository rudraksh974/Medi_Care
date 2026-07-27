import datetime
from django.db import models
from django.conf import settings

class Doctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile')
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], blank=True, null=True)
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
    experience = models.PositiveIntegerField(help_text="Years of experience", null=True, blank=True)
    location = models.CharField(max_length=255)
    phone = models.CharField(max_length=15, blank=True, null=True)
    registration_number = models.CharField(max_length=50, blank=True, null=True)
    state_council = models.CharField(max_length=100, blank=True, null=True)
    registration_year = models.PositiveIntegerField(null=True, blank=True, help_text="Year of registration with the Medical Council")
    verification_document = models.FileField(upload_to='doctor_certificates/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    appointment_mode_preference = models.CharField(
        max_length=20,
        choices=[
            ('VC', 'Video Consultation'),
            ('In-Person', 'In-Person Consultation'),
            ('Both', 'Both (Video & In-Person)'),
        ],
        default='Both'
    )
    available = models.BooleanField(default=True)
    slot_duration = models.PositiveIntegerField(default=15, help_text="Duration of one patient timing slot in minutes")

    def save(self, *args, **kwargs):
        if self.registration_year:
            current_year = datetime.date.today().year
            calculated_exp = current_year - self.registration_year
            self.experience = max(0, calculated_exp)
        else:
            self.experience = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name} ({self.specialization})"


class DoctorAvailability(models.Model):
    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='availabilities')
    day = models.CharField(max_length=15, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.doctor} - {self.day}: {self.start_time} to {self.end_time}"
    

class CachedHospital(models.Model):
    name = models.CharField(max_length=200)
    lat = models.FloatField()
    lng = models.FloatField()
    address = models.CharField(max_length=300, blank=True)
    facility_type = models.CharField(max_length=50, default='Hospital')
    fetched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CachedQuery(models.Model):
    lat = models.FloatField()
    lng = models.FloatField()
    radius = models.IntegerField()
    fetched_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Query ({self.lat}, {self.lng}) R={self.radius}"


class GeocodingCache(models.Model):
    query = models.CharField(max_length=255, unique=True)
    lat = models.FloatField()
    lng = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.query} -> ({self.lat}, {self.lng})"
