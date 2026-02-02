from datetime import timedelta
from django.utils.timezone import now
from doctors.models import Doctor, CachedHospital
from doctors import osm_api
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect
from .forms import DoctorProfileForm


@login_required
def doctor_list(request):
    doctors = Doctor.objects.filter(available=True)

    # Cache data upto (24 hours)
    cache_time = now() - timedelta(hours=24)

    cached = CachedHospital.objects.filter(fetched_at__gte=cache_time)

    if cached.exists():
        # Use cached data
        external_doctors = list(cached.values(
            "name", "lat", "lng", "address"
        ))
        print("USING CACHED OSM DATA")

    else:
        # Cache empty or expired → call API
        external_doctors = osm_api.get_nearby_hospitals(28.6315, 77.2167)
        print("FETCHING FROM OSM API")

        # Clear old cache
        CachedHospital.objects.all().delete()

        # Save new cache
        for doc in external_doctors:
            CachedHospital.objects.create(
                name=doc["name"],
                lat=doc["lat"],
                lng=doc["lng"],
                address=doc["address"]
            )

    return render(request, "doctors/doctor_list.html", {
        "doctors": doctors,
        "external_doctors": external_doctors
    })


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
