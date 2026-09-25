from django.contrib.auth.models import User
from rest_framework import serializers
from django.db import transaction

from .models import Profile, RiskZone, Alert


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    phone = serializers.CharField(max_length=30)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, write_only=True)
    preferred_area = serializers.CharField(
        max_length=160,
        required=False,
        allow_blank=True
    )
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)

    @transaction.atomic
    def create(self, validated_data):
        # Get and remove User-related fields
        name = validated_data.pop("name")
        email = validated_data.pop("email").lower().strip()
        password = validated_data.pop("password")

        # Check if email already exists
        if (
            User.objects.filter(username=email).exists()
            or User.objects.filter(email=email).exists()
        ):
            raise serializers.ValidationError({
                "email": "An account with this email already exists."
            })

        # Split full name
        parts = name.split(" ", 1)

        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

        # Create Django User
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Create Profile
        Profile.objects.create(
            user=user,
            phone=validated_data.get("phone"),
            preferred_area=validated_data.get("preferred_area", ""),
            latitude=validated_data.get("latitude"),
            longitude=validated_data.get("longitude"),
            location_enabled=validated_data.get("latitude") is not None
        )

        return user


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    phone = serializers.CharField(source="profile.phone")
    preferred_area = serializers.CharField(source="profile.preferred_area")
    latitude = serializers.FloatField(
        source="profile.latitude",
        allow_null=True
    )
    longitude = serializers.FloatField(
        source="profile.longitude",
        allow_null=True
    )
    location_enabled = serializers.BooleanField(
        source="profile.location_enabled"
    )
    language = serializers.CharField(
        source="profile.language"
    )
    notifications_enabled = serializers.BooleanField(
        source="profile.notifications_enabled"
    )
    sound_enabled = serializers.BooleanField(
        source="profile.sound_enabled"
    )
    vibration_enabled = serializers.BooleanField(
        source="profile.vibration_enabled"
    )
    last_location_at = serializers.DateTimeField(
        source="profile.last_location_at",
        allow_null=True
    )

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "email",
            "is_staff",
            "phone",
            "preferred_area",
            "latitude",
            "longitude",
            "location_enabled",
            "language",
            "notifications_enabled",
            "sound_enabled",
            "vibration_enabled",
            "last_location_at",
        ]

    def get_name(self, obj):
        return obj.get_full_name() or obj.email


class LocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class RiskZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskZone
        fields = [
            "id",
            "name",
            "hazard_type",
            "risk_level",
            "risk_score",
            "latitude",
            "longitude",
            "radius_km",
            "boundary",
            "reason",
            "rainfall",
            "soil_moisture",
            "ground_movement",
            "terrain",
            "active",
            "updated_at",
        ]


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            "id",
            "hazard_type",
            "risk_level",
            "title",
            "message",
            "latitude",
            "longitude",
            "status",
            "created_at",
            "read_at",
            "risk_zone",
        ]