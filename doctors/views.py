from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Doctor
from .forms import DoctorProfileForm


@login_required
def edit_doctor_profile(request):
    doctor = Doctor.objects.get(user=request.user)

    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            return redirect('doctor_dashboard')
    else:
        form = DoctorProfileForm(instance=doctor)

    return render(request, 'doctors/edit_profile.html', {'form': form})

@login_required
def doctor_list(request):
    doctors = Doctor.objects.filter(available=True)
    return render(request, 'doctors/doctor_list.html', {'doctors': doctors})