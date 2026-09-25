from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import JsonResponse
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from .models import Profile, RiskZone, Alert
from .serializers import RegisterSerializer, UserSerializer, LocationSerializer, RiskZoneSerializer, AlertSerializer
from .utils import distance_km, risk_rank, risk_level_from_score
from .live_data import get_live_data

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)

def make_alerts_for_user(user, lat, lon):
    profile = user.profile
    zones = RiskZone.objects.filter(active=True)
    created = []
    for zone in zones:
        d = distance_km(lat, lon, zone.latitude, zone.longitude)
        if d <= zone.radius_km and risk_rank(zone.risk_level) >= 3:
            recent = Alert.objects.filter(user=user, risk_zone=zone, created_at__gte=timezone.now()-timezone.timedelta(minutes=30)).exists()
            if not recent:
                title = f"{zone.risk_level} {zone.hazard_type} risk"
                message = zone.reason or f"Your current location is within approximately {zone.radius_km:g} km of an active {zone.hazard_type.lower()} risk zone."
                created.append(Alert.objects.create(user=user, risk_zone=zone, hazard_type=zone.hazard_type, risk_level=zone.risk_level, title=title, message=message, latitude=lat, longitude=lon))
    return created

def health(request):
    return JsonResponse({"status": "ok", "service": "SURAKSHA NER API"})

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        token, _ = Token.objects.get_or_create(user=user)
        return JsonResponse({"message": "Account created", "token": token.key, "user": UserSerializer(user).data}, status=201)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = str(request.data.get("email", "")).lower().strip()
        password = request.data.get("password", "")

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return JsonResponse(
                {"detail": "Invalid email or password."},
                status=400
            )

        user = authenticate(
            username=user.username,
            password=password
        )

        if not user:
            return JsonResponse(
                {"detail": "Invalid email or password."},
                status=400
            )

        token, _ = Token.objects.get_or_create(user=user)

        return JsonResponse({
            "message": "Login successful",
            "token": token.key,
            "is_admin": user.is_staff,
            "user": UserSerializer(user).data
        })

class MeView(APIView):
    def get(self, request):
        return JsonResponse(UserSerializer(request.user).data)
    def patch(self, request):
        profile = request.user.profile
        if "name" in request.data:
            parts = str(request.data["name"]).strip().split(" ", 1)
            request.user.first_name = parts[0] if parts else ""
            request.user.last_name = parts[1] if len(parts) > 1 else ""
            request.user.save()
        for field in ["phone", "preferred_area", "language", "notifications_enabled", "sound_enabled", "vibration_enabled"]:
            if field in request.data:
                setattr(profile, field, request.data[field])
        profile.save()
        return JsonResponse(UserSerializer(request.user).data)

class LocationUpdateView(APIView):
    def post(self, request):
        s = LocationSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        lat = s.validated_data["latitude"]
        lon = s.validated_data["longitude"]

        profile, created = Profile.objects.get_or_create(
            user=request.user,
            defaults={
                "phone": "",
                "preferred_area": "",
            }
        )

        profile.latitude = lat
        profile.longitude = lon
        profile.location_enabled = True
        profile.last_location_at = timezone.now()
        profile.save()

        new_alerts = make_alerts_for_user(
            request.user,
            lat,
            lon
        )

        return JsonResponse({
            "message": "Location updated",
            "location": {
                "latitude": lat,
                "longitude": lon,
                "updated_at": profile.last_location_at
            },
            "new_alerts": AlertSerializer(
                new_alerts,
                many=True
            ).data
        })
    
class LiveDataView(APIView):
    """Return live weather and configured official disaster-feed data.

    The endpoint never fabricates official data. If IMD credentials are not
    configured, the weather provider is explicitly reported as Open-Meteo.
    SACHET is enabled only when SACHET_CAP_URL is configured.
    """
    def get(self, request):
        try:
            lat = float(request.query_params.get("lat"))
            lon = float(request.query_params.get("lon"))
        except (TypeError, ValueError):
            profile = request.user.profile
            lat, lon = profile.latitude, profile.longitude

        if lat is None or lon is None:
            return JsonResponse({"detail": "Location is required. Provide lat/lon or enable location."}, status=400)

        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return JsonResponse({"detail": "Invalid latitude or longitude."}, status=400)

        return JsonResponse(get_live_data(lat, lon))


class RiskZoneListCreateView(APIView):
    def get(self, request):
        qs = RiskZone.objects.filter(active=True)
        return JsonResponse({"results": RiskZoneSerializer(qs, many=True).data})
    def post(self, request):
        if not request.user.is_staff: return JsonResponse({"detail": "Admin access required."}, status=403)
        s = RiskZoneSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        zone = s.save()
        return JsonResponse(RiskZoneSerializer(zone).data, status=201)

class RiskZoneDetailView(APIView):
    def get(self, request, pk):
        try: zone = RiskZone.objects.get(pk=pk)
        except RiskZone.DoesNotExist: return JsonResponse({"detail": "Risk zone not found."}, status=404)
        return JsonResponse(RiskZoneSerializer(zone).data)
    def patch(self, request, pk):
        if not request.user.is_staff: return JsonResponse({"detail": "Admin access required."}, status=403)
        try: zone = RiskZone.objects.get(pk=pk)
        except RiskZone.DoesNotExist: return JsonResponse({"detail": "Risk zone not found."}, status=404)
        s = RiskZoneSerializer(zone, data=request.data, partial=True); s.is_valid(raise_exception=True); zone=s.save()
        return JsonResponse(RiskZoneSerializer(zone).data)

class CurrentRiskView(APIView):
    def get(self, request):
        try:
            lat = float(request.query_params.get("lat")); lon = float(request.query_params.get("lon"))
        except (TypeError, ValueError):
            p = request.user.profile
            lat, lon = p.latitude, p.longitude
        if lat is None or lon is None:
            return JsonResponse({"risk_level": "LOW", "risk_score": 0, "hazards": [], "message": "Location not available."})
        matches=[]
        for zone in RiskZone.objects.filter(active=True):
            d=distance_km(lat,lon,zone.latitude,zone.longitude)
            if d <= zone.radius_km:
                matches.append({"zone": zone, "distance_km": round(d,2)})
        matches.sort(key=lambda x: (risk_rank(x["zone"].risk_level), x["zone"].risk_score), reverse=True)
        if not matches:
            return JsonResponse({"risk_level":"LOW","risk_score":0,"hazards":[],"message":"No active risk zone matched your current location."})
        top=matches[0]["zone"]
        hazards=[{"hazard_type":m["zone"].hazard_type,"risk_level":m["zone"].risk_level,"risk_score":m["zone"].risk_score,"reason":m["zone"].reason,"distance_km":m["distance_km"]} for m in matches]
        return JsonResponse({"risk_level":top.risk_level,"risk_score":top.risk_score,"reason":top.reason,"hazards":hazards})

class AlertListView(APIView):
    def get(self, request):
        qs=request.user.alerts.all()[:50]
        return JsonResponse({"results": AlertSerializer(qs,many=True).data})

class AlertReadView(APIView):
    def post(self, request, pk):
        try: a=request.user.alerts.get(pk=pk)
        except Alert.DoesNotExist: return JsonResponse({"detail":"Alert not found."},status=404)
        a.status="READ"; a.read_at=timezone.now(); a.save(update_fields=["status","read_at"])
        return JsonResponse(AlertSerializer(a).data)

class AdminSummaryView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        return JsonResponse({"users":User.objects.filter(is_staff=False).count(),"active_alerts":Alert.objects.filter(status="NEW").count(),"high_critical_zones":RiskZone.objects.filter(active=True,risk_level__in=["HIGH","CRITICAL"]).count(),"critical_zones":RiskZone.objects.filter(active=True,risk_level="CRITICAL").count()})

class AdminUsersView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        qs=User.objects.filter(is_staff=False).select_related("profile").order_by("-date_joined")[:200]
        return JsonResponse({"results":UserSerializer(qs,many=True).data})

class AdminAlertsView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        qs=Alert.objects.select_related("user","risk_zone").all()[:200]
        data=[]
        for a in qs:
            item=AlertSerializer(a).data; item["user_email"]=a.user.email; item["user_name"]=a.user.get_full_name() or a.user.email; data.append(item)
        return JsonResponse({"results":data})
