import requests

OVERPASS_URL = "https://overpass.kumi.systems/api/interpreter"
# print(" OSM API FILE LOADED ")

HEADERS = {
    "User-Agent": "MediPredict/1.0 (learning-project)",
    "Accept": "application/json"
}

def get_nearby_hospitals(lat, lng, radius=8000):
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
        results.append({
            "name": tags.get("name", "Unknown Hospital"),
            "lat": el.get("lat"),
            "lng": el.get("lon"),
            "address": tags.get("addr:street", "Address not available")
        })

    return results
