from django.test import TestCase
from django.contrib.auth import get_user_model
from users.forms import DoctorSignupForm
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class DoctorSignupTest(TestCase):
    def test_doctor_signup_form_validation(self):
        dummy_file = SimpleUploadedFile("cert.pdf", b"file_content", content_type="application/pdf")
        form_data = {
            'username': 'testdoctor',
            'email': 'doctor@example.com',
            'first_name': 'Test',
            'last_name': 'Doctor',
            'specialization': 'General Physician',
            'appointment_mode_preference': 'Both',
            'location': 'Delhi',
            'registration_number': 'MCI-12345',
            'state_council': 'Delhi Medical Council',
            'password1': 'doctorpass123',
            'password2': 'doctorpass123',
        }
        form = DoctorSignupForm(data=form_data, files={'verification_document': dummy_file})
        self.assertTrue(form.is_valid(), form.errors.as_json())
        
        otp_form_data = form_data.copy()
        otp_form = DoctorSignupForm(data=otp_form_data)
        otp_form.fields['verification_document'].required = False
        self.assertTrue(otp_form.is_valid(), otp_form.errors.as_json())
        user = otp_form.save()
        self.assertEqual(user.username, 'testdoctor')
