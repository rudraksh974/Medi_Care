import requests
from django.conf import settings
from math import radians, cos, sin, asin, sqrt
from django.utils.timezone import now
from datetime import timedelta
from doctors.models import CachedHospital, CachedQuery, GeocodingCache

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
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
    return results

def save_hospitals_to_cache(lat, lng, radius, hospitals):
    """
    Saves the fetched hospitals to CachedHospital (avoiding duplicates)
    and creates a CachedQuery entry.
    """
    if not hospitals:
        # Do not cache empty query results, to allow retries in case of temporary API failures/timeouts
        return

    for h in hospitals:
        h_lat = h["lat"]
        h_lng = h["lng"]
        h_name = h["name"]
        h_address = h.get("address", "")
        h_type = h.get("facility_type", "Hospital")

        # Check if this hospital is already cached (matching name and within 100m)
        delta = 0.0009
        exists = CachedHospital.objects.filter(
            name=h_name,
            lat__gte=h_lat - delta,
            lat__lte=h_lat + delta,
            lng__gte=h_lng - delta,
            lng__lte=h_lng + delta
        ).exists()

        if not exists:
            CachedHospital.objects.create(
                name=h_name,
                lat=h_lat,
                lng=h_lng,
                address=h_address,
                facility_type=h_type
            )

    # Save or update the CachedQuery
    CachedQuery.objects.update_or_create(
        lat=lat,
        lng=lng,
        radius=radius
    )

def get_nearby_hospitals(lat, lng, radius=5000):
    query = f"""
    [out:json][timeout:15];
    (
      node["amenity"="hospital"](around:{radius},{lat},{lng});
      node["amenity"="clinic"](around:{radius},{lat},{lng});
      node["amenity"="doctors"](around:{radius},{lat},{lng});
      node["amenity"="dentist"](around:{radius},{lat},{lng});
    );
    out;
    """

    data = None
    for url in OVERPASS_URLS:
        try:
            print(f"Trying Overpass API: {url}")
            response = requests.get(
                url,
                params={"data": query},
                headers=HEADERS,
                timeout=12
            )
            response.raise_for_status()
            data = response.json()
            break
        except Exception as e:
            print(f"OSM ERROR on {url}: {e}")
            continue

    if not data:
        print("All Overpass API endpoints failed or timed out.")
        return []

    results = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        
        # Determine category / facility_type
        amenity = tags.get("amenity", "hospital")
        if amenity == "hospital":
            facility_type = "Hospital"
        elif amenity == "clinic":
            facility_type = "Clinic"
        elif amenity == "doctors":
            facility_type = "Doctor"
        elif amenity == "dentist":
            facility_type = "Dentist"
        else:
            facility_type = "Hospital"
            
        # improved address construction
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
        
        # If still empty, try to use valid city context if available from user query (passed down? No, just keep simple)
        if full_address == "Address not available" and tags.get("check_date"):
             # Sometimes 'check_date' implies existence but no address. 
             pass

        name = tags.get("name")
        if not name or name.lower() in ["unknown hospital", "hospital", "unknown clinic", "clinic", "unknown doctor", "doctor", "unknown dentist", "dentist"]:
            continue

        results.append({
            "name": name,
            "lat": el.get("lat"),
            "lng": el.get("lon"),
            "address": full_address,
            "facility_type": facility_type
        })

    return results
