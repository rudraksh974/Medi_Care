from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from users.decorators import patient_required, doctor_required
from doctors.models import Doctor
from .models import Appointment
from django.contrib import messages
import json

@patient_required
def book_appointment(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)

    if request.method == "POST":
        date_time = request.POST.get("appointment_time")
        mode = request.POST.get("appointment_mode", "Offline")

        # Backend validation
        try:
            from datetime import datetime
            from django.utils.timezone import make_aware, now
            from django.conf import settings
            
            dt = datetime.strptime(date_time, '%Y-%m-%dT%H:%M')
            if settings.USE_TZ:
                dt = make_aware(dt)
                
            # 1. Date in the future
            if dt <= now():
                messages.error(request, "Selected appointment slot must be in the future.")
                return redirect("book_appointment", doctor_id=doctor.id)
                
            # 2. Weekday name
            weekday = dt.strftime('%A')
            
            # 3. Check day availability
            day_slots = doctor.availabilities.filter(day=weekday)
            if not day_slots.exists():
                messages.error(request, f"The doctor is not available on {weekday}s.")
                return redirect("book_appointment", doctor_id=doctor.id)
                
            # 4. Check time slot
            time_of_day = dt.time()
            is_valid_time = False
            for slot in day_slots:
                if slot.start_time <= time_of_day <= slot.end_time:
                    is_valid_time = True
                    break
                    
            if not is_valid_time:
                messages.error(request, f"Selected time is outside the doctor's available timings on {weekday}s.")
                return redirect("book_appointment", doctor_id=doctor.id)
                
            # 5. Check consultation mode
            allowed_mode = doctor.appointment_mode_preference
            if allowed_mode == 'VC' and mode != 'Online':
                messages.error(request, "This doctor only accepts Video Consultations.")
                return redirect("book_appointment", doctor_id=doctor.id)
            elif allowed_mode == 'In-Person' and mode != 'Offline':
                messages.error(request, "This doctor only accepts In-Clinic consultations.")
                return redirect("book_appointment", doctor_id=doctor.id)
                
        except Exception as e:
            messages.error(request, f"Validation error: {e}")
            return redirect("book_appointment", doctor_id=doctor.id)

        Appointment.objects.create(
            patient=request.user,
            doctor=doctor,
            appointment_time=date_time,
            appointment_mode=mode
        )
        return redirect("patient_appointments")

    # Serialize availability for JavaScript validation
    availabilities_list = []
    for s in doctor.availabilities.all():
        availabilities_list.append({
            'day': s.day,
            'start_time': s.start_time.strftime('%H:%M'),
            'end_time': s.end_time.strftime('%H:%M')
        })
    availabilities_json = json.dumps(availabilities_list)

    # Fetch approved future bookings
    from django.utils.timezone import now
    booked_slots = Appointment.objects.filter(
        doctor=doctor,
        appointment_time__gte=now(),
        status='Approved'
    ).order_by('appointment_time')

    booked_slots_list = [slot.appointment_time.strftime('%Y-%m-%dT%H:%M') for slot in booked_slots]
    booked_slots_json = json.dumps(booked_slots_list)

    return render(request, "appointments/book_appointment.html", {
        "doctor": doctor,
        "availabilities": doctor.availabilities.all().order_by('day', 'start_time'),
        "availabilities_json": availabilities_json,
        "booked_slots": booked_slots,
        "booked_slots_json": booked_slots_json,
        "slot_duration": doctor.slot_duration
    })

@patient_required
def patient_appointments(request):
    appointments = Appointment.objects.filter(patient=request.user)
    return render(request, "appointments/patient_appointments.html", {
        "appointments": appointments
    })

@doctor_required
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