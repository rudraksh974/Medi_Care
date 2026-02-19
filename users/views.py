from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, DoctorSignupForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from .decorators import patient_required, doctor_required
from .utils import send_otp_email
from django.contrib import messages



from doctors.models import Doctor

User = get_user_model()

# PATIENT SIGNUP
def patient_signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            otp = send_otp_email(email)
            
            if otp:
                # Store data in session
                request.session['signup_data'] = request.POST
                request.session['signup_otp'] = otp
                request.session['signup_role'] = 'patient'
                return redirect('verify_otp')
            else:
                messages.error(request, "Error sending OTP. Please try again.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/signup.html', {
        'form': form,
        'role': 'patient'
    })


# DOCTOR SIGNUP
def doctor_signup_view(request):
    if request.method == 'POST':
        form = DoctorSignupForm(request.POST)
        if form.is_valid():
            # Send OTP
            email = form.cleaned_data.get('email')
            otp = send_otp_email(email)
            
            if otp:
                # Store data in session
                request.session['signup_data'] = request.POST
                request.session['signup_otp'] = otp
                request.session['signup_role'] = 'doctor'
                return redirect('verify_otp')
            else:
                messages.error(request, "Error sending OTP. Please try again.")
    else:
        form = DoctorSignupForm()

    return render(request, 'users/signup.html', {
        'form': form,
        'role': 'doctor'
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
                    login(request, user)
                    
                    # Cleanup session
                    del request.session['signup_data']
                    del request.session['signup_otp']
                    del request.session['signup_role']
                    
                    return redirect('patient_dashboard')

            elif role == 'doctor':
                form = DoctorSignupForm(signup_data)
                if form.is_valid():
                    user = form.save(commit=False)
                    user.is_doctor = True
                    user.is_patient = False
                    user.save()

                    location = form.cleaned_data.get('location', 'Not set')
                    Doctor.objects.create(
                        user=user,
                        specialization='General',
                        experience=0,
                        location=location
                    )
                    login(request, user)
                    
                    # Cleanup session
                    del request.session['signup_data']
                    del request.session['signup_otp']
                    del request.session['signup_role']
                    
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
    return render(request, 'users/patient_dashboard.html')

@doctor_required
def doctor_dashboard(request):
    return render(request, 'users/doctor_dashboard.html')


# PATIENT DASHBOARD
@login_required
def patient_dashboard(request):
    return render(request, 'users/patient_dashboard.html')


# DOCTOR DASHBOARD
@login_required
def doctor_dashboard(request):
    return render(request, 'users/doctor_dashboard.html')
