from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from .decorators import patient_required, doctor_required


from doctors.models import Doctor

User = get_user_model()

# PATIENT SIGNUP
def patient_signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_patient = True
            user.is_doctor = False
            user.save()
            login(request, user)
            return redirect('patient_dashboard')
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/signup.html', {
        'form': form,
        'role': 'patient'
    })


# DOCTOR SIGNUP
def doctor_signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_doctor = True
            user.is_patient = False
            user.save()

            Doctor.objects.create(
                user=user,
                specialization='General',
                experience=0,
                location='Not set'
            )

            login(request, user)
            return redirect('doctor_dashboard')
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/signup.html', {
        'form': form,
        'role': 'doctor'
    })



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
