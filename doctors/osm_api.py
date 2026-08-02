import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.conf import settings
from math import radians, cos, sin, asin, sqrt
from django.utils.timezone import now
from datetime import timedelta
from doctors.models import CachedHospital, CachedQuery, GeocodingCache

OVERPASS_URLS = [
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter"
]
# print(" OSM API FILE LOADED ")

HEADERS = {
    "User-Agent": "MediPredict/1.0 (learning-project)",
    "Accept": "application/json"
}

def haversine_distance(lat1, lng1, lat2, lng2):
    """
    Calculate the great circle distance in meters between two points 
    on the earth (specified in decimal degrees)
    """
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlng = lng2 - lng1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371000 # Radius of earth in meters
    return c * r

def get_coordinates(place_name):
    # Check cache first
    place_name_clean = place_name.strip().lower()
    cached = GeocodingCache.objects.filter(query=place_name_clean).first()
    if cached:
        return cached.lat, cached.lng

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": place_name,
        "format": "json",
        "limit": 1
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data:
            lat = float(data[0]["lat"])
            lng = float(data[0]["lon"])
            # Save to cache
            GeocodingCache.objects.update_or_create(
                query=place_name_clean,
                defaults={"lat": lat, "lng": lng}
            )
            return lat, lng
    except Exception as e:
        print(f"Geocoding Error: {e}")
        
    return None

def get_cached_hospitals(lat, lng, radius):
    """
    Checks if we have already queried the API for this location and radius.
    If so, returns the list of CachedHospitals within the radius.
    Otherwise, returns None.
    """
    time_threshold = now() - timedelta(hours=24)
    
    # 1 degree of latitude is roughly 111,000 meters
    delta_lat_query = 1000 / 111000.0
    cos_lat = cos(radians(lat))
    delta_lng_query = 1000 / (111000.0 * cos_lat) if cos_lat != 0 else 1000 / 111000.0

    recent_queries = CachedQuery.objects.filter(
        lat__gte=lat - delta_lat_query,
        lat__lte=lat + delta_lat_query,
        lng__gte=lng - delta_lng_query,
        lng__lte=lng + delta_lng_query,
        radius__gte=radius,
        fetched_at__gte=time_threshold
    )

    cache_hit = False
    for q in recent_queries:
        if haversine_distance(lat, lng, q.lat, q.lng) <= 1000:
            cache_hit = True
            break
            
    if not cache_hit:
        return None

    # Retrieve from CachedHospital using bounding box
    delta_lat_hosp = radius / 111000.0
    delta_lng_hosp = radius / (111000.0 * cos_lat) if cos_lat != 0 else radius / 111000.0

    candidates = CachedHospital.objects.filter(
        lat__gte=lat - delta_lat_hosp,
        lat__lte=lat + delta_lat_hosp,
        lng__gte=lng - delta_lng_hosp,
        lng__lte=lng + delta_lng_hosp
    )

    results = []
    for h in candidates:
        dist = haversine_distance(lat, lng, h.lat, h.lng)
        if dist <= radius:
            results.append({
                "name": h.name,
                "lat": h.lat,
                "lng": h.lng,
                "address": h.address,
                "facility_type": h.facility_type
            })
    return results if results else None

def save_hospitals_to_cache(lat, lng, radius, hospitals):
    """
    Saves the fetched hospitals to CachedHospital (avoiding duplicates)
    and creates a CachedQuery entry using bulk database operations.
    """
    if not hospitals:
        # Do not cache empty query results, to allow retries in case of temporary API failures/timeouts
        return

    try:
        delta_lat_hosp = radius / 111000.0
        cos_lat = cos(radians(lat))
        delta_lng_hosp = radius / (111000.0 * cos_lat) if cos_lat != 0 else radius / 111000.0

        existing_names = set(
            CachedHospital.objects.filter(
                lat__gte=lat - delta_lat_hosp,
                lat__lte=lat + delta_lat_hosp,
                lng__gte=lng - delta_lng_hosp,
                lng__lte=lng + delta_lng_hosp
            ).values_list('name', flat=True)
        )

        new_hospitals = []
        for h in hospitals:
            h_name = h["name"]
            if h_name not in existing_names:
                existing_names.add(h_name)
                new_hospitals.append(
                    CachedHospital(
                        name=h_name,
                        lat=h["lat"],
                        lng=h["lng"],
                        address=h.get("address", ""),
                        facility_type=h.get("facility_type", "Hospital")
                    )
                )

        if new_hospitals:
            CachedHospital.objects.bulk_create(new_hospitals, ignore_conflicts=True)

        CachedQuery.objects.update_or_create(
            lat=lat,
            lng=lng,
            radius=radius
        )
    except Exception as e:
        print(f"Error saving hospitals to cache: {e}")

def _fetch_nominatim_fallback(lat, lng, radius):
    try:
        print(f"Fallback: Fetching from Nominatim API (Location: {lat}, {lng})")
        delta_lat = radius / 111000.0
        cos_lat = cos(radians(lat))
        delta_lng = radius / (111000.0 * cos_lat) if cos_lat != 0 else radius / 111000.0

        viewbox = f"{lng - delta_lng:.4f},{lat + delta_lat:.4f},{lng + delta_lng:.4f},{lat - delta_lat:.4f}"
        
        results = []
        seen_names = set()

        for amenity in ["hospital", "clinic", "doctors", "dentist"]:
            try:
                resp = requests.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "amenity": amenity,
                        "format": "json",
                        "viewbox": viewbox,
                        "bounded": 1,
                        "limit": 30
                    },
                    headers=HEADERS,
                    timeout=5
                )
                if resp.status_code == 200:
                    for item in resp.json():
                        raw_name = item.get("display_name", "").split(",")[0].strip()
                        if not raw_name or raw_name.lower() in ["unknown hospital", "hospital", "unknown clinic", "clinic"]:
                            continue
                        if raw_name in seen_names:
                            continue
                        seen_names.add(raw_name)

                        lat_val = float(item.get("lat"))
                        lng_val = float(item.get("lon"))

                        if amenity == "clinic":
                            fac_type = "Clinic"
                        elif amenity == "doctors":
                            fac_type = "Doctor"
                        elif amenity == "dentist":
                            fac_type = "Dentist"
                        else:
                            fac_type = "Hospital"

                        results.append({
                            "name": raw_name,
                            "lat": lat_val,
                            "lng": lng_val,
                            "address": item.get("display_name", "Address not available"),
                            "facility_type": fac_type
                        })
            except Exception as ex:
                print(f"Nominatim sub-fetch error for {amenity}: {ex}")

        return results
    except Exception as e:
        print(f"Nominatim fallback error: {e}")
        return []

def get_nearby_hospitals(lat, lng, radius=5000):
    try:
        # Cap radius to max 15,000 meters to prevent massive Overpass payloads and server timeouts
        radius = min(int(radius), 15000)

        query = f"""
        [out:json][timeout:6];
        nwr["amenity"~"hospital|clinic|doctors|dentist"](around:{radius},{lat},{lng});
        out center qt 150;
        """

        def _fetch_url(url):
            try:
                print(f"Trying Overpass API: {url}")
                response = requests.get(
                    url,
                    params={"data": query},
                    headers=HEADERS,
                    timeout=5
                )
                if response.status_code == 200:
                    json_data = response.json()
                    if json_data and json_data.get("elements"):
                        return json_data
            except Exception as e:
                print(f"OSM ERROR on {url}: {e}")
            return None

        data = None
        with ThreadPoolExecutor(max_workers=len(OVERPASS_URLS)) as executor:
            futures = [executor.submit(_fetch_url, url) for url in OVERPASS_URLS]
            for future in as_completed(futures):
                res = future.result()
                if res and not data:
                    data = res
                    break

        if not data:
            print("All Overpass API endpoints timed out. Using Nominatim API fallback...")
            return _fetch_nominatim_fallback(lat, lng, radius)

        results = []
        seen_names = set()
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            
            name = tags.get("name")
            if not name or name.lower() in ["unknown hospital", "hospital", "unknown clinic", "clinic", "unknown doctor", "doctor", "unknown dentist", "dentist"]:
                continue

            if name in seen_names:
                continue
            seen_names.add(name)

            lat_val = el.get("lat") or el.get("center", {}).get("lat")
            lng_val = el.get("lon") or el.get("center", {}).get("lon")

            if lat_val is None or lng_val is None:
                continue

            amenity_val = str(tags.get("amenity") or tags.get("healthcare") or "hospital").lower()
            name_lower = name.lower()

            if "dentist" in amenity_val or "dental" in name_lower or "dentist" in name_lower:
                facility_type = "Dentist"
            elif "clinic" in amenity_val or "clinic" in name_lower or "polyclinic" in name_lower or "centre" in amenity_val or "center" in amenity_val:
                facility_type = "Clinic"
            elif "doctor" in amenity_val or "dr." in name_lower or "dr " in name_lower:
                facility_type = "Doctor"
            else:
                facility_type = "Hospital"
                
            address_parts = []
            if tags.get("addr:housenumber"):
                address_parts.append(tags.get("addr:housenumber"))
            if tags.get("addr:street"):
                address_parts.append(tags.get("addr:street"))
            if tags.get("addr:suburb"):
                 address_parts.append(tags.get("addr:suburb"))
            if tags.get("addr:city"):
                address_parts.append(tags.get("addr:city"))
            
            full_address = ", ".join(address_parts) if address_parts else tags.get("addr:full", "Address not available")

            results.append({
                "name": name,
                "lat": lat_val,
                "lng": lng_val,
                "address": full_address,
                "facility_type": facility_type
            })

        if not results:
            return _fetch_nominatim_fallback(lat, lng, radius)

        return results
    except Exception as e:
        print(f"Error in get_nearby_hospitals: {e}")
        return _fetch_nominatim_fallback(lat, lng, radius)
