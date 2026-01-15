from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

def patient_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_patient:
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return wrapper


def doctor_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_doctor:
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return wrapper
