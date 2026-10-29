import math
import urllib.request
import urllib.parse
import json
from typing import List, Dict, Any, Optional, Tuple

GEOAPIFY_API_KEY = "0bd3f31be0ee48fea21d7f2abb2e2987"
DEFAULT_WARANGAL_LAT = 18.002476
DEFAULT_WARANGAL_LON = 79.556723

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes exact spherical distance in kilometers between two geographic coordinates
    using the Haversine formula.
    """
    R = 6371.0 # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)

def geocode_address(address: str) -> Tuple[float, float, str]:
    """
    Geocodes an address string using Geoapify Geocoding API with proximity bias to Warangal.
    Falls back gracefully to default Warangal coordinates if lookup times out or fails.
    """
    if not address or not address.strip():
        return (DEFAULT_WARANGAL_LAT, DEFAULT_WARANGAL_LON, "Warangal, Telangana")

    try:
        clean_addr = address.strip()
        query_params = urllib.parse.urlencode({
            "text": clean_addr,
            "bias": f"proximity:{DEFAULT_WARANGAL_LON},{DEFAULT_WARANGAL_LAT}",
            "apiKey": GEOAPIFY_API_KEY
        })
        url = f"https://api.geoapify.com/v1/geocode/search?{query_params}"
        req = urllib.request.Request(url, headers={"User-Agent": "Tapza-Backend/1.0"})
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("features") and len(data["features"]) > 0:
                props = data["features"][0].get("properties", {})
                lat = float(props.get("lat", DEFAULT_WARANGAL_LAT))
                lon = float(props.get("lon", DEFAULT_WARANGAL_LON))
                formatted = props.get("formatted", clean_addr)
                return (lat, lon, formatted)
    except Exception as e:
        print(f"[GeoService] Geocoding warning: {e}. Using fallback coordinates.")

    return (DEFAULT_WARANGAL_LAT, DEFAULT_WARANGAL_LON, address.strip())

def find_pharmacies_in_radius(
    db,
    customer_lat: float,
    customer_lon: float,
    min_radius_km: float = 0.0,
    max_radius_km: float = 5.0
) -> List[Dict[str, Any]]:
    """
    Finds active pharmacies within [min_radius_km, max_radius_km] of the customer
    using SQLite R*Tree bounding box filtering + Haversine exact distance calculation.
    """
    # 1 degree latitude ~ 111 km
    delta_lat = max_radius_km / 111.0
    # 1 degree longitude ~ 111 * cos(lat) km
    cos_lat = math.cos(math.radians(customer_lat))
    if cos_lat == 0:
        cos_lat = 0.0001
    delta_lon = max_radius_km / (111.0 * abs(cos_lat))

    min_lat = customer_lat - delta_lat
    max_lat = customer_lat + delta_lat
    min_lon = customer_lon - delta_lon
    max_lon = customer_lon + delta_lon

    # Query R*Tree candidate bounding boxes
    query = """
        SELECT r.id, p.pharmacy_name, p.address, p.phone, p.latitude, p.longitude, p.is_active
        FROM pharmacy_rtree r
        JOIN pharmacy_profiles p ON r.id = p.user_id
        WHERE r.min_lat >= ? AND r.max_lat <= ?
          AND r.min_lng >= ? AND r.max_lng <= ?
          AND p.is_active = 1
    """
    rows = db.execute(query, (min_lat, max_lat, min_lon, max_lon)).fetchall()

    results = []
    for r in rows:
        p_lat = float(r["latitude"]) if r["latitude"] is not None else None
        p_lon = float(r["longitude"]) if r["longitude"] is not None else None
        if p_lat is None or p_lon is None:
            continue

        dist = haversine_distance(customer_lat, customer_lon, p_lat, p_lon)
        if (min_radius_km == 0.0 and 0.0 <= dist <= max_radius_km) or (min_radius_km > 0.0 and min_radius_km < dist <= max_radius_km):
            results.append({
                "pharmacy_id": r["id"],
                "pharmacy_name": r["pharmacy_name"],
                "address": r["address"],
                "phone": r["phone"],
                "latitude": p_lat,
                "longitude": p_lon,
                "distance_km": dist
            })

    # Sort results ascending by distance
    results.sort(key=lambda x: x["distance_km"])
    return results

def generate_radar_static_map_url(
    customer_lat: float,
    customer_lon: float,
    contacted_pharmacies: List[Dict[str, Any]],
    accepted_pharmacy_id: Optional[int] = None,
    current_radius_km: float = 5.0
) -> str:
    """
    Constructs a dynamic Geoapify Static Map URL with:
    - Customer Pin (Red, marker 'C')
    - 5km Translucent Radius Circle
    - 10km Expanded Radius Circle (if expanded)
    - Blue pins for all contacted pharmacies
    - Green Pin with checkmark for accepted pharmacy
    """
    marker_parts = []

    # 1. Customer Marker (Red)
    marker_parts.append(f"lonlat:{customer_lon},{customer_lat};color:#ef4444;text:C;size:large")

    # 2. Pharmacy Markers
    # Keep at most 25 markers to stay well within Geoapify URL length limit
    for p in contacted_pharmacies[:25]:
        p_id = p.get("pharmacy_id") or p.get("id")
        p_lat = p.get("latitude")
        p_lon = p.get("longitude")
        if p_lat is None or p_lon is None:
            continue

        if accepted_pharmacy_id and p_id == accepted_pharmacy_id:
            # Accepted pharmacy: pulsing green pin
            marker_parts.append(f"lonlat:{p_lon},{p_lat};color:#16a34a;text:✓;size:large")
        else:
            # Contacted pharmacy: standard blue pin
            marker_parts.append(f"lonlat:{p_lon},{p_lat};color:#2563eb;size:medium")

    # 3. Geometry (Circles)
    # Circle pixel radius: at zoom 12/13, 5km is ~75px, 10km is ~140px
    geometry_parts = []
    # 5km circle (Blue translucent)
    geometry_parts.append(f"circle:{customer_lon},{customer_lat},75;linecolor:#2563eb;fillcolor:#3b82f6;fillopacity:0.18;linewidth:2")
    if current_radius_km > 5.0:
        # 10km expanded circle (Amber translucent)
        geometry_parts.append(f"circle:{customer_lon},{customer_lat},140;linecolor:#d97706;fillcolor:#f59e0b;fillopacity:0.15;linewidth:2")

    markers_str = "|".join(marker_parts)
    geometry_str = "|".join(geometry_parts)

    params = {
        "style": "osm-bright-smooth",
        "width": "620",
        "height": "380",
        "center": f"lonlat:{customer_lon},{customer_lat}",
        "zoom": "12" if current_radius_km > 5.0 else "13",
        "marker": markers_str,
        "geometry": geometry_str,
        "apiKey": GEOAPIFY_API_KEY
    }

    return "https://maps.geoapify.com/v1/staticmap?" + urllib.parse.urlencode(params)
