from django import forms
from .models import Doctor

class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['experience', 'location', 'phone', 'appointment_mode_preference', 'available', 'lat', 'lng', 'slot_duration', 'registration_year']
        widgets = {
            'experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'appointment_mode_preference': forms.Select(attrs={'class': 'form-control'}),
            'available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'lat': forms.HiddenInput(),
            'lng': forms.HiddenInput(),
            'slot_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': '5', 'max': '180', 'placeholder': 'Slot duration in minutes (e.g. 15)'}),
            'registration_year': forms.NumberInput(attrs={'class': 'form-control', 'min': '1950', 'max': '2026', 'placeholder': 'Registration year (e.g. 2018)'}),
        }
