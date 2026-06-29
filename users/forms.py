from django.contrib.auth import get_user_model
from django import forms
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(required=True, label="First Name")
    email = forms.EmailField(required=True, label="Email Address")

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")

STATE_COUNCIL_CHOICES = [
    ('', 'Select State Medical Council'),
    ('National Medical Commission (NMC)', 'National Medical Commission (NMC)'),
    ('Andhra Pradesh Medical Council', 'Andhra Pradesh Medical Council'),
    ('Assam Medical Council', 'Assam Medical Council'),
    ('Bihar Medical Council', 'Bihar Medical Council'),
    ('Chhattisgarh Medical Council', 'Chhattisgarh Medical Council'),
    ('Delhi Medical Council', 'Delhi Medical Council'),
    ('Goa Medical Council', 'Goa Medical Council'),
    ('Gujarat Medical Council', 'Gujarat Medical Council'),
    ('Haryana Medical Council', 'Haryana Medical Council'),
    ('Himachal Pradesh Medical Council', 'Himachal Pradesh Medical Council'),
    ('Jammu & Kashmir Medical Council', 'Jammu & Kashmir Medical Council'),
    ('Jharkhand Medical Council', 'Jharkhand Medical Council'),
    ('Karnataka Medical Council', 'Karnataka Medical Council'),
    ('Kerala Medical Council', 'Kerala Medical Council'),
    ('Madhya Pradesh Medical Council', 'Madhya Pradesh Medical Council'),
    ('Maharashtra Medical Council', 'Maharashtra Medical Council'),
    ('Manipur Medical Council', 'Manipur Medical Council'),
    ('Mizoram Medical Council', 'Mizoram Medical Council'),
    ('Nagaland Medical Council', 'Nagaland Medical Council'),
    ('Odisha Medical Council', 'Odisha Medical Council'),
    ('Punjab Medical Council', 'Punjab Medical Council'),
    ('Rajasthan Medical Council', 'Rajasthan Medical Council'),
    ('Sikkim Medical Council', 'Sikkim Medical Council'),
    ('Tamil Nadu Medical Council', 'Tamil Nadu Medical Council'),
    ('Telangana State Medical Council', 'Telangana State Medical Council'),
    ('Tripura State Medical Council', 'Tripura State Medical Council'),
    ('Uttar Pradesh Medical Council', 'Uttar Pradesh Medical Council'),
    ('Uttarakhand Medical Council', 'Uttarakhand Medical Council'),
    ('West Bengal Medical Council', 'West Bengal Medical Council'),
]

class DoctorSignupForm(CustomUserCreationForm):
    from doctors.models import Doctor

    specialization = forms.ChoiceField(
        choices=Doctor.SPECIALIZATION_CHOICES,
        required=True,
        label="Specialization / Category"
    )
    appointment_mode_preference = forms.ChoiceField(
        choices=[
            ('VC', 'Video Consultation'),
            ('In-Person', 'In-Person Consultation'),
            ('Both', 'Both (Video & In-Person)'),
        ],
        required=True,
        label="Appointment Mode Preference",
        initial='Both'
    )
    location = forms.CharField(
        required=True, 
        label="Location / Address", 
        help_text="Pin your clinic or hospital on the map below to automatically fill this address."
    )
    lat = forms.FloatField(widget=forms.HiddenInput(), required=False)
    lng = forms.FloatField(widget=forms.HiddenInput(), required=False)
    registration_number = forms.CharField(
        required=True,
        label="Medical Registration Number",
        widget=forms.TextInput(attrs={'placeholder': 'e.g., MCI-12345 or UP-98765'})
    )
    state_council = forms.ChoiceField(
        choices=STATE_COUNCIL_CHOICES,
        required=True,
        label="State Medical Council"
    )
    verification_document = forms.FileField(
        required=True,
        label="Registration Certificate",
        help_text="Upload your medical registration certificate (PDF, JPEG, or PNG)"
    )

    class Meta(CustomUserCreationForm.Meta):
        fields = CustomUserCreationForm.Meta.fields + (
            "specialization", "appointment_mode_preference", "location", "lat", "lng",
            "registration_number", "state_council", "verification_document"
        )
