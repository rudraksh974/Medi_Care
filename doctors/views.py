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

    # Default: New Delhi
    lat, lng = 28.6315, 77.2167
    use_cache = True
    
    if lat_param and lng_param:
        # User selected a point on the map
        try:
            lat = float(lat_param)
            lng = float(lng_param)
            use_cache = False
            print(f"Searching by Coords: {lat}, {lng}, Radius: {radius}")
        except ValueError:
            print("Invalid coordinates provided")

    elif location_query:
        # User typed a location
        print(f"Searching for location: {location_query}")
        coords = osm_api.get_coordinates(location_query)
        if coords:
            lat, lng = coords
            use_cache = False # Don't use/pollute cache for custom searches
        else:
            print("Location not found, using default.")

    # Only filter registered doctors if a text location is provided
    if location_query:
         doctors = doctors.filter(location__icontains=location_query)

    # Cache data upto (24 hours)
    cache_time = now() - timedelta(hours=24)
    
    # Note: We only use cache if NO custom search (text or map) was done
    if use_cache:
        cached = CachedHospital.objects.filter(fetched_at__gte=cache_time)
        if cached.exists():
            # Use cached data
            external_doctors = list(cached.values(
                "name", "lat", "lng", "address"
            ))
            print("USING CACHED OSM DATA")
        else:
            # Cache empty or expired → call API
            external_doctors = osm_api.get_nearby_hospitals(lat, lng)
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
    else:
        # Direct fetch for custom location/coords
        print(f"FETCHING FROM OSM API (Custom Location: {lat}, {lng})")
        external_doctors = osm_api.get_nearby_hospitals(lat, lng, radius=radius)


    return render(request, "doctors/doctor_list.html", {
        "doctors": doctors,
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
