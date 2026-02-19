from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from doctors.models import Doctor
from .models import Appointment

@login_required
def book_appointment(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)

    if request.method == "POST":
        date_time = request.POST.get("appointment_time")
        mode = request.POST.get("appointment_mode", "Offline")

        Appointment.objects.create(
            patient=request.user,
            doctor=doctor,
            appointment_time=date_time,
            appointment_mode=mode
        )
        return redirect("patient_appointments")

    return render(request, "appointments/book_appointment.html", {
        "doctor": doctor
    })

@login_required
def patient_appointments(request):
    appointments = Appointment.objects.filter(patient=request.user)
    return render(request, "appointments/patient_appointments.html", {
        "appointments": appointments
    })

@login_required
def doctor_appointments(request):
    doctor = request.user.doctor_profile
    appointments = Appointment.objects.filter(doctor=doctor)

    return render(request, "appointments/doctor_appointments.html", {
        "appointments": appointments
    })

@login_required
def update_appointment_status(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Security: Check kar rha hai user valid hai ki nhi
    if appointment.doctor.user != request.user:
        return redirect("login")

    status = request.GET.get("status")
    if status in ["Approved", "Rejected"]:
        appointment.status = status
        appointment.save()

    return redirect("doctor_appointments")



@login_required
def video_call(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.user != appointment.patient and request.user != appointment.doctor.user:
        return redirect('home')

    if appointment.status != 'Approved' or appointment.appointment_mode != 'Online':
        return redirect('home')

    return render(request, 'appointments/video_call.html', {
        'appointment': appointment,
        'room_name': f"MediPredict_Call_{appointment.id}_{appointment.created_at.strftime('%Y%m%d')}",
        'user_name': request.user.get_full_name() or request.user.username
    })