from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, DoctorSignupForm, PatientProfileForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from .decorators import patient_required, doctor_required
from .utils import send_otp_email
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import time



from doctors.models import Doctor

User = get_user_model()

# PATIENT SIGNUP
def patient_signup_view(request):
    cooldown_remaining = 0
    last_sent = request.session.get('otp_cooldown_time')
    if last_sent:
        elapsed = time.time() - last_sent
        if elapsed < 30:
            cooldown_remaining = int(30 - elapsed)

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            if cooldown_remaining > 0:
                messages.error(request, f"Please wait {cooldown_remaining} seconds before requesting another OTP.")
                return render(request, 'users/signup.html', {
                    'form': form,
                    'role': 'patient',
                    'cooldown_remaining': cooldown_remaining
                })

            email = form.cleaned_data.get('email')
            otp = send_otp_email(email)
            
            if otp:
                request.session['otp_cooldown_time'] = time.time()
                # Store data in session as plain serializable dict
                request.session['signup_data'] = request.POST.dict()
                request.session['signup_otp'] = otp
                request.session['signup_role'] = 'patient'
                return redirect('verify_otp')
            else:
                messages.error(request, "Error sending OTP. Please try again.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/signup.html', {
        'form': form,
        'role': 'patient',
        'cooldown_remaining': cooldown_remaining
    })


# DOCTOR SIGNUP
def doctor_signup_view(request):
    cooldown_remaining = 0
    last_sent = request.session.get('otp_cooldown_time')
    if last_sent:
        elapsed = time.time() - last_sent
        if elapsed < 30:
            cooldown_remaining = int(30 - elapsed)

    if request.method == 'POST':
        form = DoctorSignupForm(request.POST, request.FILES)
        if form.is_valid():
            if cooldown_remaining > 0:
                messages.error(request, f"Please wait {cooldown_remaining} seconds before requesting another OTP.")
                return render(request, 'users/signup.html', {
                    'form': form,
                    'role': 'doctor',
                    'cooldown_remaining': cooldown_remaining
                })

            # Send OTP
            email = form.cleaned_data.get('email')
            otp = send_otp_email(email)
            
            if otp:
                request.session['otp_cooldown_time'] = time.time()
                # Store data in session as plain serializable dict
                request.session['signup_data'] = request.POST.dict()
                request.session['signup_otp'] = otp
                request.session['signup_role'] = 'doctor'

                
                # Save uploaded file temporarily
                if 'verification_document' in request.FILES:
                    uploaded_file = request.FILES['verification_document']
                    temp_path = default_storage.save(
                        f'temp_certificates/{uploaded_file.name}',
                        ContentFile(uploaded_file.read())
                    )
                    request.session['signup_temp_file'] = temp_path
                return redirect('verify_otp')
            else:
                messages.error(request, "Error sending OTP. Please try again.")
    else:
        form = DoctorSignupForm()

    return render(request, 'users/signup.html', {
        'form': form,
        'role': 'doctor',
        'cooldown_remaining': cooldown_remaining
    })

# OTP VERIFICATION
def verify_otp_view(request):
    if 'signup_otp' not in request.session:
        return redirect('login')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        generated_otp = request.session.get('signup_otp')

        if entered_otp == generated_otp:
            signup_data = request.session.get('signup_data')
            role = request.session.get('signup_role')

            if role == 'patient':
                form = CustomUserCreationForm(signup_data)
                if form.is_valid():
                    user = form.save(commit=False)
                    user.is_patient = True
                    user.is_doctor = False
                    user.save()
                    
                    age = form.cleaned_data.get('age')
                    gender = form.cleaned_data.get('gender')
                    
                    # Automatically create corresponding Patient profile
                    from patients.models import Patient
                    patient, created = Patient.objects.get_or_create(user=user)
                    if age is not None:
                        patient.age = age
                    if gender:
                        patient.gender = gender
                    patient.save()
                    
                    login(request, user)
                    
                    # Cleanup session safely
                    request.session.pop('signup_data', None)
                    request.session.pop('signup_otp', None)
                    request.session.pop('signup_role', None)
                    request.session.pop('otp_cooldown_time', None)
                    
                    return redirect('patient_dashboard')

            elif role == 'doctor':
                form = DoctorSignupForm(signup_data)
                form.fields['verification_document'].required = False
                if form.is_valid():
                    user = form.save(commit=False)
                    user.is_doctor = True
                    user.is_patient = False
                    user.save()

                    age = form.cleaned_data.get('age')
                    gender = form.cleaned_data.get('gender')
                    location = form.cleaned_data.get('location', 'Not set')
                    specialization = form.cleaned_data.get('specialization', 'General Physician')
                    appointment_mode_preference = form.cleaned_data.get('appointment_mode_preference', 'Both')
                    lat = form.cleaned_data.get('lat')
                    lng = form.cleaned_data.get('lng')
                    registration_number = form.cleaned_data.get('registration_number')
                    state_council = form.cleaned_data.get('state_council')
                    registration_year = form.cleaned_data.get('registration_year')
                    consultation_fee = form.cleaned_data.get('consultation_fee') or 500
                    
                    doctor = Doctor(
                        user=user,
                        age=age,
                        gender=gender,
                        specialization=specialization,
                        consultation_fee=consultation_fee,
                        appointment_mode_preference=appointment_mode_preference,
                        lat=lat,
                        lng=lng,
                        location=location,
                        registration_number=registration_number,
                        state_council=state_council,
                        registration_year=registration_year,
                        is_verified=False  # Must be manually verified by admin
                    )
                    
                    temp_file_path = request.session.get('signup_temp_file')
                    if temp_file_path and default_storage.exists(temp_file_path):
                        with default_storage.open(temp_file_path) as f:
                            doctor.verification_document.save(
                                os.path.basename(temp_file_path),
                                ContentFile(f.read()),
                                save=False
                            )
                        default_storage.delete(temp_file_path)
                    
                    doctor.save()
                    login(request, user)
                    
                    # Cleanup session safely
                    request.session.pop('signup_data', None)
                    request.session.pop('signup_otp', None)
                    request.session.pop('signup_role', None)
                    request.session.pop('signup_temp_file', None)
                    request.session.pop('otp_cooldown_time', None)
                    
                    return redirect('doctor_dashboard')
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'users/verify_otp.html')



# LOGIN (COMMON)
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard_redirect')
    else:
        form = AuthenticationForm()

    return render(request, 'users/login.html', {'form': form})


# LOGOUT
def logout_view(request):
    logout(request)
    return redirect('login')


# ROLE BASED DASHBOARD REDIRECT
@login_required
def dashboard_redirect(request):
    if request.user.is_doctor:
        return redirect('doctor_dashboard')
    elif request.user.is_patient:
        return redirect('patient_dashboard')
    else:
        return redirect('login')


@patient_required
def patient_dashboard(request):
    from patients.models import Patient
    patient, created = Patient.objects.get_or_create(user=request.user)
    return render(request, 'users/patient_dashboard.html', {'patient': patient})

@doctor_required
def doctor_dashboard(request):
    return render(request, 'users/doctor_dashboard.html')

@patient_required
def edit_patient_profile(request):
    from patients.models import Patient
    patient, created = Patient.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = PatientProfileForm(request.POST)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data.get('last_name', '')
            request.user.save(update_fields=['first_name', 'last_name'])

            patient.age = form.cleaned_data['age']
            patient.gender = form.cleaned_data['gender']
            patient.save()

            messages.success(request, "Your profile has been updated successfully.")
            return redirect('patient_dashboard')
    else:
        form = PatientProfileForm(initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'age': patient.age,
            'gender': patient.gender,
        })

    return render(request, 'users/edit_patient_profile.html', {'form': form})
