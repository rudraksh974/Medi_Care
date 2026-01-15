from django.db import models
from django.conf import settings
from doctors.models import Doctor
from patients.models import Patient

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE
    )
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    appointment_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    def __str__(self):
        return f"{self.patient} → {self.doctor}"
