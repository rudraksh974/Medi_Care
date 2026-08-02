from datetime import timedelta
from django.utils.timezone import now
from django.http import JsonResponse
from doctors.models import Doctor, CachedHospital, DoctorAvailability
from doctors import osm_api
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import DoctorProfileForm
from users.decorators import doctor_required
from django.contrib import messages


@login_required
def doctor_list(request):
    doctors = Doctor.objects.filter(available=True).prefetch_related('availabilities')

    location_query = request.GET.get('location')
    lat_param = request.GET.get('lat')
    lng_param = request.GET.get('lng')
    radius_param = request.GET.get('radius', 5000) # Default 5km

    try:
        radius = min(max(int(radius_param), 500), 15000) # Clamp radius between 500m and 15,000m
    except:
        radius = 5000

    lat = None
    lng = None

    # Check if a search was requested or if we should use cached user location
    if not lat_param and not lng_param and not location_query:
        # No search param provided, check if the user has a saved location in profile
        if request.user.last_lat and request.user.last_lng:
            lat = request.user.last_lat
            lng = request.user.last_lng
            location_query = request.user.last_location or f"({lat:.4f}, {lng:.4f})"
            print(f"Loading cached user location: {location_query} ({lat}, {lng})")
        else:
            print("First visit: no cached user location, skipping external search.")
    else:
        # Search param provided
        if lat_param and lng_param:
            try:
                lat = float(lat_param)
                lng = float(lng_param)
                if not location_query:
                    location_query = f"({lat:.4f}, {lng:.4f})"
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

    external_doctors = []
    fetch_async = False

    if lat and lng:
        # Save the searched location to the user profile if logged in
        if request.user.is_authenticated:
            try:
                request.user.last_lat = lat
                request.user.last_lng = lng
                request.user.last_location = location_query
                request.user.save(update_fields=['last_lat', 'last_lng', 'last_location'])
            except Exception as e:
                print(f"User location save error: {e}")

        # Try to retrieve from database cache first
        print(f"Checking cache for location: {lat}, {lng}")
        cached_hospitals = osm_api.get_cached_hospitals(lat, lng, radius)
        fetch_async = False
        if cached_hospitals is not None:
            print(f"CACHE HIT: Found {len(cached_hospitals)} hospitals in database.")
            external_doctors = cached_hospitals
        else:
            # Cache miss: load asynchronously via background AJAX to keep HTML page load instant (<50ms)
            print(f"CACHE MISS: Loading external facilities asynchronously via AJAX")
            external_doctors = []
            fetch_async = True

    # Filter registered doctors if location query is text-based (not coordinates)
    if location_query and not location_query.startswith("Selected on Map") and not (location_query.startswith("(") and location_query.endswith(")")):
         doctors = doctors.filter(location__icontains=location_query)

    specialization_query = request.GET.get('specialization')
    if specialization_query:
        # Map the incoming query to a standard specialization choice if possible
        mapped_specialization = None
        query_lower = specialization_query.lower()
        
        # Substring / keyword mappings
        keywords_map = {
            'cardio': 'Cardiologist',
            'heart': 'Cardiologist',
            'derma': 'Dermatologist',
            'skin': 'Dermatologist',
            'neuro': 'Neurologist',
            'brain': 'Neurologist',
            'ortho': 'Orthopedist',
            'bone': 'Orthopedist',
            'pediat': 'Pediatrician',
            'child': 'Pediatrician',
            'psych': 'Psychiatrist',
            'mental': 'Psychiatrist',
            'gyn': 'Gynecologist',
            'ent': 'ENT Specialist',
            'ear': 'ENT Specialist',
            'nose': 'ENT Specialist',
            'throat': 'ENT Specialist',
            'dentist': 'Dentist',
            'dental': 'Dentist',
            'ophthalm': 'Ophthalmologist',
            'eye': 'Ophthalmologist',
            'uro': 'Urologist',
            'gastro': 'Gastroenterologist',
            'stomach': 'Gastroenterologist',
            'pulmon': 'Pulmonologist',
            'lung': 'Pulmonologist',
            'oncol': 'Oncologist',
            'cancer': 'Oncologist',
            'physician': 'General Physician',
            'general': 'General Physician',
        }
        
        # 1. Try keyword/substring match
        for key, val in keywords_map.items():
            if key in query_lower:
                mapped_specialization = val
                break
                
        # 2. Try matching any of the choice names as a substring (e.g. if query contains choice or vice-versa)
        if not mapped_specialization:
            for choice, _ in Doctor.SPECIALIZATION_CHOICES:
                choice_lower = choice.lower()
                if choice_lower in query_lower or query_lower in choice_lower:
                    mapped_specialization = choice
                    break
        
        # If we successfully mapped it, use it for filtering and UI selection
        if mapped_specialization:
            specialization_query = mapped_specialization
            doctors = doctors.filter(specialization=specialization_query)
        else:
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
        "fetch_async": fetch_async,
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


@doctor_required
def manage_availability(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    availabilities = doctor.availabilities.all().order_by('day', 'start_time')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            days = request.POST.getlist('days')
            start_time_str = request.POST.get('start_time')
            end_time_str = request.POST.get('end_time')
            
            if not days:
                messages.error(request, "Please select at least one day.")
            else:
                try:
                    from datetime import datetime
                    start_time = datetime.strptime(start_time_str, '%H:%M').time()
                    end_time = datetime.strptime(end_time_str, '%H:%M').time()
                    
                    if start_time >= end_time:
                        messages.error(request, "Start time must be before end time.")
                    else:
                        success_days = []
                        overlap_days = []
                        
                        for day in days:
                            # Check for overlaps
                            overlaps = doctor.availabilities.filter(
                                day=day,
                                start_time__lt=end_time,
                                end_time__gt=start_time
                            ).exists()
                            
                            if overlaps:
                                overlap_days.append(day)
                            else:
                                DoctorAvailability.objects.create(
                                    doctor=doctor,
                                    day=day,
                                    start_time=start_time,
                                    end_time=end_time
                                )
                                success_days.append(day)
                        
                        if success_days:
                            messages.success(request, f"Availability added for: {', '.join(success_days)}.")
                        if overlap_days:
                            messages.error(request, f"Overlap detected on: {', '.join(overlap_days)}. These slots were not added.")
                except Exception as e:
                    messages.error(request, f"Invalid time format: {e}")
                
        elif action == 'delete':
            availability_id = request.POST.get('availability_id')
            slot = get_object_or_404(DoctorAvailability, id=availability_id, doctor=doctor)
            slot.delete()
            messages.success(request, "Availability slot removed.")
            
        return redirect('manage_availability')
        
    # Group availabilities by day for nice rendering
    grouped_availabilities = {}
    for day, _ in DoctorAvailability.DAY_CHOICES:
        grouped_availabilities[day] = availabilities.filter(day=day)

    return render(request, 'doctors/manage_availability.html', {
        'doctor': doctor,
        'grouped_availabilities': grouped_availabilities,
        'days_of_week': [d[0] for d in DoctorAvailability.DAY_CHOICES]
    })


@login_required
def api_nearby_hospitals(request):
    lat_param = request.GET.get('lat')
    lng_param = request.GET.get('lng')
    radius_param = request.GET.get('radius', 5000)

    try:
        lat = float(lat_param)
        lng = float(lng_param)
        radius = min(max(int(radius_param), 500), 15000)
    except (TypeError, ValueError):
        return JsonResponse({'hospitals': [], 'error': 'Invalid parameters'}, status=400)

    # 1. Check database cache first
    cached_hospitals = osm_api.get_cached_hospitals(lat, lng, radius)
    if cached_hospitals is not None:
        return JsonResponse({'hospitals': cached_hospitals, 'source': 'cache'})

    # 2. Fast concurrent fetch from external OSM API
    try:
        hospitals = osm_api.get_nearby_hospitals(lat, lng, radius=radius)
        osm_api.save_hospitals_to_cache(lat, lng, radius, hospitals)
        return JsonResponse({'hospitals': hospitals, 'source': 'api'})
    except Exception as e:
        print(f"API Error fetching hospitals: {e}")
        return JsonResponse({'hospitals': [], 'error': str(e)})
