from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):

    LANGUAGE_CHOICES = [
        ("English", "English"),
        ("हिन्दी", "हिन्दी"),
        ("অসমীয়া", "অসমীয়া"),
        ("বাংলা", "বাংলা"),
        ("नेपाली", "नेपाली"),
        ("মণিপুরী", "মণিপুরী"),
        ("Khasi", "Khasi"),
        ("Mizo", "Mizo"),
        ("Bodo", "Bodo"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    phone = models.CharField(
        max_length=30,
        blank=True
    )

    preferred_area = models.CharField(
        max_length=160,
        blank=True
    )

    latitude = models.FloatField(
        null=True,
        blank=True
    )

    longitude = models.FloatField(
        null=True,
        blank=True
    )

    location_enabled = models.BooleanField(
        default=False
    )

    language = models.CharField(
        max_length=40,
        choices=LANGUAGE_CHOICES,
        default="English"
    )

    notifications_enabled = models.BooleanField(
        default=True
    )

    sound_enabled = models.BooleanField(
        default=True
    )

    vibration_enabled = models.BooleanField(
        default=True
    )

    last_location_at = models.DateTimeField(
        null=True,
        blank=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.user.email or self.user.username


class RiskZone(models.Model):

    HAZARD_CHOICES = [
        ("Landslide", "Landslide"),
        ("Flood", "Flood"),
        ("Very Heavy Rainfall", "Very Heavy Rainfall"),
    ]

    RISK_CHOICES = [
        ("LOW", "LOW"),
        ("MODERATE", "MODERATE"),
        ("HIGH", "HIGH"),
        ("CRITICAL", "CRITICAL"),
    ]

    name = models.CharField(
        max_length=160
    )

    hazard_type = models.CharField(
        max_length=40,
        choices=HAZARD_CHOICES
    )

    risk_level = models.CharField(
        max_length=10,
        choices=RISK_CHOICES
    )

    risk_score = models.PositiveIntegerField(
        default=0
    )

    latitude = models.FloatField()

    longitude = models.FloatField()

    radius_km = models.FloatField(
        default=10
    )

    # GIS polygon
    # Format:
    # [
    #   [longitude, latitude],
    #   [longitude, latitude],
    #   ...
    # ]
    boundary = models.JSONField(
        default=list,
        blank=True
    )

    reason = models.TextField(
        blank=True
    )

    rainfall = models.PositiveIntegerField(
        default=0
    )

    soil_moisture = models.PositiveIntegerField(
        default=0
    )

    ground_movement = models.PositiveIntegerField(
        default=0
    )

    terrain = models.PositiveIntegerField(
        default=0
    )

    active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "-risk_score",
            "-updated_at"
        ]

    def __str__(self):
        return (
            f"{self.name} - "
            f"{self.hazard_type} - "
            f"{self.risk_level}"
        )


class Alert(models.Model):

    STATUS_CHOICES = [
        ("NEW", "NEW"),
        ("READ", "READ"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="alerts"
    )

    risk_zone = models.ForeignKey(
        RiskZone,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="alerts"
    )

    hazard_type = models.CharField(
        max_length=40
    )

    risk_level = models.CharField(
        max_length=10
    )

    title = models.CharField(
        max_length=180
    )

    message = models.TextField()

    latitude = models.FloatField(
        null=True,
        blank=True
    )

    longitude = models.FloatField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="NEW"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = [
            "-created_at"
        ]

    def __str__(self):
        return (
            f"{self.user.email}: "
            f"{self.title}"
        )