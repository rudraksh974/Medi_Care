import requests
from django.conf import settings

OVERPASS_URL = "https://overpass.kumi.systems/api/interpreter"
# print(" OSM API FILE LOADED ")

HEADERS = {
    "User-Agent": "MediPredict/1.0 (learning-project)",
    "Accept": "application/json"
}

def get_coordinates(place_name):
    """
    Convert a place name (city, address) to lat/lng using Nominatim.
    """
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
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"Geocoding Error: {e}")
        
    return None

def get_nearby_hospitals(lat, lng, radius=5000):
    """
    Fetch hospitals from OSM within a given radius (meters).
    """
    query = f"""
    [out:json][timeout:25];
    node["amenity"="hospital"](around:{radius},{lat},{lng});
    out;
    """

    try:
        response = requests.get(
            OVERPASS_URL,
            params={"data": query},
            headers=HEADERS,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("OSM ERROR:", e)
        return []

    results = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        
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
        if not name:
            continue

        results.append({
            "name": name,
            "lat": el.get("lat"),
            "lng": el.get("lon"),
            "address": full_address
        })

    return results
