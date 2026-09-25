import math


# =========================================================
# DISTANCE
# =========================================================

def distance_km(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Haversine distance between two GPS coordinates.
    Returns distance in kilometres.
    """

    lat1 = float(lat1)
    lon1 = float(lon1)
    lat2 = float(lat2)
    lon2 = float(lon2)

    radius = 6371.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    d_phi = math.radians(
        lat2 - lat1
    )

    d_lambda = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(d_phi / 2) ** 2
        +
        math.cos(phi1)
        *
        math.cos(phi2)
        *
        math.sin(d_lambda / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return radius * c


# =========================================================
# RISK RANK
# =========================================================

def risk_rank(level):

    values = {
        "LOW": 1,
        "MODERATE": 2,
        "HIGH": 3,
        "CRITICAL": 4,
    }

    return values.get(
        str(level).upper(),
        0
    )


# =========================================================
# RISK LEVEL FROM SCORE
# =========================================================

def risk_level_from_score(score):

    score = float(score)

    if score >= 80:
        return "CRITICAL"

    if score >= 60:
        return "HIGH"

    if score >= 30:
        return "MODERATE"

    return "LOW"


# =========================================================
# POINT IN POLYGON
# =========================================================

def point_in_polygon(
    lat,
    lon,
    polygon
):
    """
    Ray-casting polygon geofencing.

    Polygon format:

    [
        [longitude, latitude],
        [longitude, latitude],
        ...
    ]
    """

    if not polygon:
        return False

    if len(polygon) < 3:
        return False

    try:

        x = float(lon)
        y = float(lat)

        inside = False

        j = len(polygon) - 1

        for i in range(len(polygon)):

            xi = float(
                polygon[i][0]
            )

            yi = float(
                polygon[i][1]
            )

            xj = float(
                polygon[j][0]
            )

            yj = float(
                polygon[j][1]
            )

            intersects = (
                ((yi > y) != (yj > y))
                and
                (
                    x
                    <
                    (
                        (xj - xi)
                        *
                        (y - yi)
                        /
                        ((yj - yi) or 1e-12)
                    )
                    + xi
                )
            )

            if intersects:
                inside = not inside

            j = i

        return inside

    except (
        TypeError,
        ValueError,
        IndexError
    ):

        return False


# =========================================================
# GEO-FENCE CHECK
# =========================================================

def check_geofence(
    lat,
    lon,
    zone
):
    """
    Polygon gets priority.

    If polygon exists:
        polygon geofencing is used.

    Otherwise:
        circular radius fallback is used.
    """

    inside_polygon = False

    if zone.boundary:

        inside_polygon = point_in_polygon(
            lat,
            lon,
            zone.boundary
        )

        if inside_polygon:

            distance = distance_km(
                lat,
                lon,
                zone.latitude,
                zone.longitude
            )

            return {
                "matched": True,
                "geofence_type": "polygon",
                "inside_polygon": True,
                "distance_km": round(
                    distance,
                    2
                )
            }

        return {
            "matched": False,
            "geofence_type": "polygon",
            "inside_polygon": False,
            "distance_km": round(
                distance_km(
                    lat,
                    lon,
                    zone.latitude,
                    zone.longitude
                ),
                2
            )
        }

    distance = distance_km(
        lat,
        lon,
        zone.latitude,
        zone.longitude
    )

    inside_radius = (
        distance <= zone.radius_km
    )

    return {
        "matched": inside_radius,
        "geofence_type": "radius",
        "inside_polygon": False,
        "distance_km": round(
            distance,
            2
        )
    }


# =========================================================
# WEATHER SCORE
# =========================================================

def rainfall_score(rainfall):

    rainfall = float(
        rainfall or 0
    )

    if rainfall >= 60:
        return 100

    if rainfall >= 40:
        return 80

    if rainfall >= 20:
        return 60

    if rainfall >= 10:
        return 40

    if rainfall > 0:
        return 20

    return 0


def humidity_score(humidity):

    humidity = float(
        humidity or 0
    )

    if humidity >= 90:
        return 100

    if humidity >= 80:
        return 70

    if humidity >= 70:
        return 40

    return 0


def calculate_weather_score(
    rainfall,
    humidity
):

    r_score = rainfall_score(
        rainfall
    )

    h_score = humidity_score(
        humidity
    )

    score = (
        r_score * 0.75
        +
        h_score * 0.25
    )

    return round(
        score
    )


# =========================================================
# PERSONALIZED WARNING
# =========================================================

def build_personalized_warning(
    risk_level,
    hazard_type,
    zone_name,
    rainfall,
    humidity,
    distance,
    geofence_type,
    official_alert_count=0
):

    messages = []

    if risk_level == "CRITICAL":

        title = (
            f"CRITICAL {hazard_type} WARNING"
        )

        messages.append(
            "Immediate safety precautions are advised."
        )

    elif risk_level == "HIGH":

        title = (
            f"HIGH {hazard_type} RISK"
        )

        messages.append(
            "High-risk conditions have been detected near your location."
        )

    elif risk_level == "MODERATE":

        title = (
            f"MODERATE {hazard_type} RISK"
        )

        messages.append(
            "Monitor local conditions and official advisories."
        )

    else:

        title = (
            f"LOW {hazard_type} RISK"
        )

        messages.append(
            "No immediate high-risk condition was detected."
        )

    if rainfall >= 40:

        messages.append(
            f"Live rainfall: {rainfall:.1f} mm."
        )

    elif rainfall > 0:

        messages.append(
            f"Rainfall detected: {rainfall:.1f} mm."
        )

    if humidity >= 80:

        messages.append(
            f"High humidity: {humidity:.0f}%."
        )

    if zone_name:

        messages.append(
            f"Matched risk zone: {zone_name}."
        )

    if distance is not None:

        messages.append(
            f"Approximate distance from zone centre: "
            f"{distance:.2f} km."
        )

    if geofence_type == "polygon":

        messages.append(
            "Your location is inside the GIS risk-zone polygon."
        )

    elif geofence_type == "radius":

        messages.append(
            "Your location is inside the configured risk radius."
        )

    if official_alert_count > 0:

        messages.append(
            f"{official_alert_count} official SACHET/NDMA "
            "NER alert(s) are currently available."
        )

    messages.append(
        "Follow official emergency instructions and move "
        "to a safer location if authorities advise evacuation."
    )

    return {
        "title": title,
        "message": " ".join(messages)
    }