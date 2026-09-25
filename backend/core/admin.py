from django.contrib import admin
from .models import Profile, RiskZone, Alert

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "preferred_area", "latitude", "longitude", "location_enabled", "last_location_at")
    search_fields = ("user__email", "user__first_name", "phone", "preferred_area")

@admin.register(RiskZone)
class RiskZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "hazard_type", "risk_level", "risk_score", "latitude", "longitude", "radius_km", "active")
    list_filter = ("hazard_type", "risk_level", "active")
    search_fields = ("name", "reason")

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("user", "hazard_type", "risk_level", "title", "status", "created_at")
    list_filter = ("hazard_type", "risk_level", "status")
    search_fields = ("user__email", "title", "message")
