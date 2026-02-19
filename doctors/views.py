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

    location_query = request.GET.get('location')
    lat_param = request.GET.get('lat')
    lng_param = request.GET.get('lng')
    radius_param = request.GET.get('radius', 5000) # Default 5km

    try:
        radius = int(radius_param)
    except:
        radius = 5000

    # Remove Default Location (lat, lng = None)
    lat, lng = None, None
    external_doctors = []
    
    if lat_param and lng_param:
        try:
            lat = float(lat_param)
            lng = float(lng_param)
            print(f"Searching by Coords: {lat}, {lng}, Radius: {radius}")
        except ValueError:
            print("Invalid coordinates provided")

    elif location_query:
        print(f"Searching for location: {location_query}")
        coords = osm_api.get_coordinates(location_query)
        if coords:
            lat, lng = coords
        else:
            print("Location not found.")

    # Only filter registered doctors if a text location is provided
    if location_query:
         doctors = doctors.filter(location__icontains=location_query)

    if lat and lng:
        # Direct fetch for custom location/coords
        print(f"FETCHING FROM OSM API (Custom Location: {lat}, {lng})")
        external_doctors = osm_api.get_nearby_hospitals(lat, lng, radius=radius)


    specialization_query = request.GET.get('specialization')
    if specialization_query:
        doctors = doctors.filter(specialization=specialization_query)
    specializations = [c[0] for c in Doctor.SPECIALIZATION_CHOICES]

    return render(request, "doctors/doctor_list.html", {
        "doctors": doctors,
        "specializations": specializations,
        "selected_specialization": specialization_query,
        "external_doctors": external_doctors,
        "current_location": location_query or "",
        "current_lat": lat,
        "current_lng": lng,
        "current_radius": radius,
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
