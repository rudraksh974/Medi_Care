from django import forms
from .models import Doctor

class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['specialization', 'experience', 'location', 'phone', 'available']
