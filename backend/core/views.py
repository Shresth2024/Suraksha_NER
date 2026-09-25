from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone

from rest_framework import permissions
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView

from .models import (
    Profile,
    RiskZone,
    Alert
)

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    LocationSerializer,
    RiskZoneSerializer,
    AlertSerializer
)

from .utils import (
    distance_km,
    risk_rank,
    risk_level_from_score,
    check_geofence,
    calculate_weather_score,
    build_personalized_warning
)

from .live_data import get_live_data

from .ml_risk import (
    predict_risk,
    risk_level as ml_risk_level
)


# =========================================================
# ADMIN PERMISSION
# =========================================================

class IsAdminUser(
    permissions.BasePermission
):

    def has_permission(
        self,
        request,
        view
    ):

        return bool(
            request.user
            and
            request.user.is_authenticated
            and
            request.user.is_staff
        )


# =========================================================
# FIND MATCHING RISK ZONES
# =========================================================

def get_matching_zones(
    lat,
    lon
):

    matches = []

    zones = RiskZone.objects.filter(
        active=True
    )

    for zone in zones:

        geo = check_geofence(
            lat,
            lon,
            zone
        )

        if geo["matched"]:

            matches.append({

                "zone": zone,

                "distance_km":
                    geo["distance_km"],

                "geofence_type":
                    geo["geofence_type"],

                "inside_polygon":
                    geo["inside_polygon"]

            })


    matches.sort(

        key=lambda item: (

            risk_rank(
                item["zone"].risk_level
            ),

            item["zone"].risk_score

        ),

        reverse=True

    )


    return matches


# =========================================================
# BUILD COMPLETE RISK RESULT
# =========================================================

def calculate_current_risk(
    lat,
    lon
):

    # -----------------------------------------------------
    # 1. GIS / GEOFENCING
    # -----------------------------------------------------

    matches = get_matching_zones(
        lat,
        lon
    )


    # No zone
    if not matches:

        return {

            "risk_level": "LOW",

            "risk_score": 0,

            "reason":
                "No active GIS risk zone matched your current location.",

            "hazards": [],

            "location": {

                "latitude": lat,

                "longitude": lon

            },

            "live_data": {

                "available": False

            },

            "risk_engine": {

                "type":
                    "AI + GIS + live weather",

                "matched_zone":
                    False

            }

        }


    # -----------------------------------------------------
    # 2. LIVE WEATHER
    # -----------------------------------------------------

    live = get_live_data(
        lat,
        lon
    )

    weather = (
        live.get(
            "weather",
            {}
        )
        or {}
    )


    rainfall = float(
        weather.get(
            "rainfall_mm",
            0
        )
        or 0
    )


    humidity = float(
        weather.get(
            "humidity_percent",
            0
        )
        or 0
    )


    temperature = weather.get(
        "temperature_c"
    )


    wind = weather.get(
        "wind_kmh"
    )


    weather_score = (
        calculate_weather_score(
            rainfall,
            humidity
        )
    )


    # -----------------------------------------------------
    # 3. SACHET OFFICIAL ALERT COUNT
    # -----------------------------------------------------

    official = (
        live.get(
            "official_alerts",
            {}
        )
        or {}
    )


    official_alerts = (
        official.get(
            "alerts",
            []
        )
        or []
    )


    official_alert_count = len(
        official_alerts
    )


    # -----------------------------------------------------
    # 4. AI / ML PREDICTION
    # -----------------------------------------------------

    top = matches[0]["zone"]


    ml_score = predict_risk(

        rainfall=rainfall,

        soil_moisture=top.soil_moisture,

        ground_movement=top.ground_movement,

        terrain=top.terrain,

        base_risk=top.risk_score,

        humidity=humidity

    )


    # -----------------------------------------------------
    # 5. COMBINE AI + WEATHER
    # -----------------------------------------------------

    combined_score = (

        ml_score * 0.75

        +

        weather_score * 0.25

    )


    # -----------------------------------------------------
    # 6. OFFICIAL ALERT BOOST
    # -----------------------------------------------------

    # Official alerts support the warning layer.
    # We don't blindly convert every India-wide alert
    # into local danger.

    official_boost = 0


    if official_alert_count > 0:

        official_boost = 5


    final_score = min(

        100,

        round(
            combined_score
            +
            official_boost
        )

    )


    # -----------------------------------------------------
    # 7. FINAL RISK LEVEL
    # -----------------------------------------------------

    final_level = ml_risk_level(
        final_score
    )


    # Never downgrade a critical configured zone

    if top.risk_level == "CRITICAL":

        final_level = "CRITICAL"

        final_score = max(
            final_score,
            80
        )


    # -----------------------------------------------------
    # 8. REASON
    # -----------------------------------------------------

    reasons = []


    if rainfall >= 40:

        reasons.append(

            f"Heavy live rainfall "
            f"({rainfall:.1f} mm)"

        )

    elif rainfall > 0:

        reasons.append(

            f"Live rainfall "
            f"({rainfall:.1f} mm)"

        )


    if humidity >= 80:

        reasons.append(

            f"High humidity "
            f"({humidity:.0f}%)"

        )


    if official_alert_count:

        reasons.append(

            f"{official_alert_count} official "
            "SACHET/NDMA alert(s) available"

        )


    reasons.append(

        f"GIS matched zone: {top.name}"

    )


    reasons.append(

        f"AI predicted risk: {ml_score}/100"

    )


    reason = " • ".join(
        reasons
    )


    # -----------------------------------------------------
    # 9. HAZARDS
    # -----------------------------------------------------

    hazards = []


    for item in matches:

        zone = item["zone"]


        if zone.id == top.id:

            zone_level = final_level

            zone_score = final_score

            zone_reason = reason

        else:

            zone_level = zone.risk_level

            zone_score = zone.risk_score

            zone_reason = (
                zone.reason
                or
                f"Active {zone.hazard_type.lower()} "
                "risk zone."
            )


        hazards.append({

            "hazard_type":
                zone.hazard_type,

            "risk_level":
                zone_level,

            "risk_score":
                zone_score,

            "reason":
                zone_reason,

            "distance_km":
                item["distance_km"],

            "geofence_type":
                item["geofence_type"],

            "inside_polygon":
                item["inside_polygon"],

            "zone_name":
                zone.name

        })


    # -----------------------------------------------------
    # 10. FINAL RESPONSE
    # -----------------------------------------------------

    return {

        "risk_level":
            final_level,

        "risk_score":
            final_score,

        "reason":
            reason,

        "location": {

            "latitude":
                lat,

            "longitude":
                lon

        },

        "matched_zone": {

            "id":
                top.id,

            "name":
                top.name,

            "hazard_type":
                top.hazard_type,

            "geofence_type":
                matches[0][
                    "geofence_type"
                ],

            "inside_polygon":
                matches[0][
                    "inside_polygon"
                ],

            "distance_km":
                matches[0][
                    "distance_km"
                ]

        },

        "hazards":
            hazards,

        "live_data": {

            "provider":
                weather.get(
                    "provider"
                ),

            "official":
                weather.get(
                    "official",
                    False
                ),

            "available":
                weather.get(
                    "available",
                    False
                ),

            "temperature_c":
                temperature,

            "humidity_percent":
                humidity,

            "rainfall_mm":
                rainfall,

            "wind_kmh":
                wind,

            "weather_score":
                weather_score

        },

        "official_alerts": {

            "provider":
                official.get(
                    "provider",
                    "SACHET / NDMA"
                ),

            "configured":
                official.get(
                    "configured",
                    False
                ),

            "count":
                official_alert_count,

            "alerts":
                official_alerts[:5]

        },

        "ai_prediction": {

            "model":
                "RandomForestRegressor",

            "score":
                ml_score,

            "inputs": {

                "rainfall":
                    rainfall,

                "soil_moisture":
                    top.soil_moisture,

                "ground_movement":
                    top.ground_movement,

                "terrain":
                    top.terrain,

                "base_risk":
                    top.risk_score,

                "humidity":
                    humidity

            }

        },

        "risk_engine": {

            "type":
                "AI + Live Weather + GIS + Official Alerts",

            "ml_weight":
                0.75,

            "weather_weight":
                0.25,

            "official_alert_boost":
                official_boost

        }

    }


# =========================================================
# PERSONALIZED ALERT CREATION
# =========================================================

def make_alerts_for_user(
    user,
    lat,
    lon,
    risk_data=None
):

    if risk_data is None:

        risk_data = calculate_current_risk(
            lat,
            lon
        )


    created = []


    risk_level = risk_data.get(
        "risk_level",
        "LOW"
    )


    if risk_level not in [
        "HIGH",
        "CRITICAL"
    ]:

        return created


    matched_zone = (
        risk_data.get(
            "matched_zone"
        )
        or {}
    )


    zone_id = matched_zone.get(
        "id"
    )


    zone = None


    if zone_id:

        try:

            zone = RiskZone.objects.get(
                id=zone_id
            )

        except RiskZone.DoesNotExist:

            zone = None


    hazard_type = (
        matched_zone.get(
            "hazard_type"
        )
        or
        "Multi-Hazard"
    )


    zone_name = (
        matched_zone.get(
            "name"
        )
        or
        "Nearby risk zone"
    )


    distance = matched_zone.get(
        "distance_km"
    )


    geofence_type = (
        matched_zone.get(
            "geofence_type"
        )
        or
        "unknown"
    )


    live_data = (
        risk_data.get(
            "live_data",
            {}
        )
        or {}
    )


    rainfall = float(
        live_data.get(
            "rainfall_mm",
            0
        )
        or 0
    )


    humidity = float(
        live_data.get(
            "humidity_percent",
            0
        )
        or 0
    )


    official_count = int(
        (
            risk_data.get(
                "official_alerts",
                {}
            )
            or {}
        ).get(
            "count",
            0
        )
        or 0
    )


    warning = build_personalized_warning(

        risk_level=
            risk_level,

        hazard_type=
            hazard_type,

        zone_name=
            zone_name,

        rainfall=
            rainfall,

        humidity=
            humidity,

        distance=
            distance,

        geofence_type=
            geofence_type,

        official_alert_count=
            official_count

    )


    recent_exists = Alert.objects.filter(

        user=user,

        risk_zone=zone,

        created_at__gte=
            timezone.now()
            -
            timezone.timedelta(
                minutes=30
            )

    ).exists()


    if recent_exists:

        return created


    alert = Alert.objects.create(

        user=user,

        risk_zone=zone,

        hazard_type=
            hazard_type,

        risk_level=
            risk_level,

        title=
            warning["title"],

        message=
            warning["message"],

        latitude=
            lat,

        longitude=
            lon

    )


    created.append(
        alert
    )


    return created


# =========================================================
# HEALTH
# =========================================================

def health(request):

    return JsonResponse({

        "status":
            "ok",

        "service":
            "SURAKSHA NER API"

    })


# =========================================================
# REGISTER
# =========================================================

class RegisterView(APIView):

    permission_classes = [
        permissions.AllowAny
    ]


    def post(
        self,
        request
    ):

        serializer = RegisterSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = serializer.save()


        token, _ = Token.objects.get_or_create(
            user=user
        )


        return JsonResponse({

            "message":
                "Account created",

            "token":
                token.key,

            "user":
                UserSerializer(
                    user
                ).data

        }, status=201)


# =========================================================
# LOGIN
# =========================================================

class LoginView(APIView):

    permission_classes = [
        permissions.AllowAny
    ]


    def post(
        self,
        request
    ):

        email = str(
            request.data.get(
                "email",
                ""
            )
        ).lower().strip()


        password = request.data.get(
            "password",
            ""
        )


        try:

            user = User.objects.get(
                email__iexact=email
            )

        except User.DoesNotExist:

            return JsonResponse({

                "detail":
                    "Invalid email or password."

            }, status=400)


        user = authenticate(

            username=user.username,

            password=password

        )


        if not user:

            return JsonResponse({

                "detail":
                    "Invalid email or password."

            }, status=400)


        token, _ = Token.objects.get_or_create(
            user=user
        )


        return JsonResponse({

            "message":
                "Login successful",

            "token":
                token.key,

            "is_admin":
                user.is_staff,

            "user":
                UserSerializer(
                    user
                ).data

        })


# =========================================================
# PROFILE
# =========================================================

class MeView(APIView):

    def get(
        self,
        request
    ):

        return JsonResponse(
            UserSerializer(
                request.user
            ).data
        )


    def patch(
        self,
        request
    ):

        profile = request.user.profile


        if "name" in request.data:

            parts = str(
                request.data["name"]
            ).strip().split(
                " ",
                1
            )


            request.user.first_name = (
                parts[0]
                if parts
                else ""
            )


            request.user.last_name = (
                parts[1]
                if len(parts) > 1
                else ""
            )


            request.user.save()


        allowed = [

            "phone",

            "preferred_area",

            "language",

            "notifications_enabled",

            "sound_enabled",

            "vibration_enabled"

        ]


        for field in allowed:

            if field in request.data:

                setattr(

                    profile,

                    field,

                    request.data[field]

                )


        profile.save()


        return JsonResponse(
            UserSerializer(
                request.user
            ).data
        )


# =========================================================
# LOCATION UPDATE
# =========================================================

class LocationUpdateView(APIView):

    def post(
        self,
        request
    ):

        serializer = LocationSerializer(
            data=request.data
        )


        serializer.is_valid(
            raise_exception=True
        )


        lat = serializer.validated_data[
            "latitude"
        ]


        lon = serializer.validated_data[
            "longitude"
        ]


        profile, _ = (
            Profile.objects.get_or_create(

                user=request.user,

                defaults={

                    "phone":
                        "",

                    "preferred_area":
                        ""

                }

            )
        )


        profile.latitude = lat

        profile.longitude = lon

        profile.location_enabled = True

        profile.last_location_at = (
            timezone.now()
        )

        profile.save()


        # COMPLETE RISK ENGINE

        risk_data = calculate_current_risk(
            lat,
            lon
        )


        # PERSONALIZED ALERT

        new_alerts = make_alerts_for_user(

            request.user,

            lat,

            lon,

            risk_data

        )


        return JsonResponse({

            "message":
                "Location updated",

            "location": {

                "latitude":
                    lat,

                "longitude":
                    lon,

                "updated_at":
                    profile.last_location_at

            },

            "risk":
                risk_data,

            "new_alerts":
                AlertSerializer(
                    new_alerts,
                    many=True
                ).data

        })


# =========================================================
# LIVE DATA
# =========================================================

class LiveDataView(APIView):

    def get(
        self,
        request
    ):

        try:

            lat = float(
                request.query_params.get(
                    "lat"
                )
            )

            lon = float(
                request.query_params.get(
                    "lon"
                )
            )

        except (
            TypeError,
            ValueError
        ):

            profile = request.user.profile

            lat = profile.latitude

            lon = profile.longitude


        if lat is None or lon is None:

            return JsonResponse({

                "detail":
                    "Location is required."

            }, status=400)


        return JsonResponse(
            get_live_data(
                lat,
                lon
            )
        )


# =========================================================
# CURRENT RISK
# =========================================================

class CurrentRiskView(APIView):

    def get(
        self,
        request
    ):

        try:

            lat = float(
                request.query_params.get(
                    "lat"
                )
            )

            lon = float(
                request.query_params.get(
                    "lon"
                )
            )

        except (
            TypeError,
            ValueError
        ):

            profile = request.user.profile

            lat = profile.latitude

            lon = profile.longitude


        if lat is None or lon is None:

            return JsonResponse({

                "risk_level":
                    "LOW",

                "risk_score":
                    0,

                "hazards":
                    [],

                "message":
                    "Location not available."

            })


        risk_data = calculate_current_risk(
            lat,
            lon
        )


        # Automatically create personalized
        # alert when current risk is HIGH/CRITICAL.

        make_alerts_for_user(

            request.user,

            lat,

            lon,

            risk_data

        )


        return JsonResponse(
            risk_data
        )


# =========================================================
# RISK ZONES
# =========================================================

class RiskZoneListCreateView(APIView):

    def get(
        self,
        request
    ):

        zones = RiskZone.objects.filter(
            active=True
        )


        return JsonResponse({

            "results":
                RiskZoneSerializer(
                    zones,
                    many=True
                ).data

        })


    def post(
        self,
        request
    ):

        if not request.user.is_staff:

            return JsonResponse({

                "detail":
                    "Admin access required."

            }, status=403)


        serializer = RiskZoneSerializer(
            data=request.data
        )


        serializer.is_valid(
            raise_exception=True
        )


        zone = serializer.save()


        return JsonResponse(

            RiskZoneSerializer(
                zone
            ).data,

            status=201

        )


# =========================================================
# RISK ZONE DETAIL
# =========================================================

class RiskZoneDetailView(APIView):

    def get(
        self,
        request,
        pk
    ):

        try:

            zone = RiskZone.objects.get(
                pk=pk
            )

        except RiskZone.DoesNotExist:

            return JsonResponse({

                "detail":
                    "Risk zone not found."

            }, status=404)


        return JsonResponse(
            RiskZoneSerializer(
                zone
            ).data
        )


    def patch(
        self,
        request,
        pk
    ):

        if not request.user.is_staff:

            return JsonResponse({

                "detail":
                    "Admin access required."

            }, status=403)


        try:

            zone = RiskZone.objects.get(
                pk=pk
            )

        except RiskZone.DoesNotExist:

            return JsonResponse({

                "detail":
                    "Risk zone not found."

            }, status=404)


        serializer = RiskZoneSerializer(

            zone,

            data=request.data,

            partial=True

        )


        serializer.is_valid(
            raise_exception=True
        )


        zone = serializer.save()


        return JsonResponse(
            RiskZoneSerializer(
                zone
            ).data
        )


# =========================================================
# ALERT LIST
# =========================================================

class AlertListView(APIView):

    def get(
        self,
        request
    ):

        alerts = request.user.alerts.all()[:50]


        return JsonResponse({

            "results":
                AlertSerializer(
                    alerts,
                    many=True
                ).data

        })


# =========================================================
# MARK ALERT READ
# =========================================================

class AlertReadView(APIView):

    def post(
        self,
        request,
        pk
    ):

        try:

            alert = request.user.alerts.get(
                pk=pk
            )

        except Alert.DoesNotExist:

            return JsonResponse({

                "detail":
                    "Alert not found."

            }, status=404)


        alert.status = "READ"

        alert.read_at = timezone.now()

        alert.save(
            update_fields=[
                "status",
                "read_at"
            ]
        )


        return JsonResponse(
            AlertSerializer(
                alert
            ).data
        )


# =========================================================
# ADMIN SUMMARY
# =========================================================

class AdminSummaryView(APIView):

    permission_classes = [
        IsAdminUser
    ]


    def get(
        self,
        request
    ):

        return JsonResponse({

            "users":
                User.objects
                .filter(
                    is_staff=False
                )
                .count(),

            "active_alerts":
                Alert.objects
                .filter(
                    status="NEW"
                )
                .count(),

            "high_critical_zones":
                RiskZone.objects
                .filter(
                    active=True,
                    risk_level__in=[
                        "HIGH",
                        "CRITICAL"
                    ]
                )
                .count(),

            "critical_zones":
                RiskZone.objects
                .filter(
                    active=True,
                    risk_level="CRITICAL"
                )
                .count()

        })


# =========================================================
# ADMIN USERS
# =========================================================

class AdminUsersView(APIView):

    permission_classes = [
        IsAdminUser
    ]


    def get(
        self,
        request
    ):

        users = (
            User.objects
            .filter(
                is_staff=False
            )
            .select_related(
                "profile"
            )
            .order_by(
                "-date_joined"
            )[:200]
        )


        return JsonResponse({

            "results":
                UserSerializer(
                    users,
                    many=True
                ).data

        })


# =========================================================
# ADMIN ALERTS
# =========================================================

class AdminAlertsView(APIView):

    permission_classes = [
        IsAdminUser
    ]


    def get(
        self,
        request
    ):

        alerts = (
            Alert.objects
            .select_related(
                "user",
                "risk_zone"
            )
            .all()[:200]
        )


        data = []


        for alert in alerts:

            item = AlertSerializer(
                alert
            ).data


            item["user_email"] = (
                alert.user.email
            )


            item["user_name"] = (
                alert.user.get_full_name()
                or
                alert.user.email
            )


            data.append(
                item
            )


        return JsonResponse({

            "results":
                data

        })