from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [("auth", "0012_alter_user_first_name_max_length")]
    operations = [
        migrations.CreateModel(name="Profile", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("phone", models.CharField(blank=True, max_length=30)),
            ("preferred_area", models.CharField(blank=True, max_length=160)),
            ("latitude", models.FloatField(blank=True, null=True)),
            ("longitude", models.FloatField(blank=True, null=True)),
            ("location_enabled", models.BooleanField(default=False)),
            ("language", models.CharField(choices=[("English","English"),("हिन्दी","हिन्दी"),("অসমীয়া","অসমীয়া"),("বাংলা","বাংলা"),("नेपाली","नेपाली"),("মণিপুরী","মণিপুরী"),("Khasi","Khasi"),("Mizo","Mizo"),("Bodo","Bodo")], default="English", max_length=40)),
            ("notifications_enabled", models.BooleanField(default=True)),
            ("sound_enabled", models.BooleanField(default=True)),
            ("vibration_enabled", models.BooleanField(default=True)),
            ("last_location_at", models.DateTimeField(blank=True, null=True)),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to="auth.user")),
        ]),
        migrations.CreateModel(name="RiskZone", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=160)),
            ("hazard_type", models.CharField(choices=[("Landslide","Landslide"),("Flood","Flood"),("Very Heavy Rainfall","Very Heavy Rainfall")], max_length=40)),
            ("risk_level", models.CharField(choices=[("LOW","LOW"),("MODERATE","MODERATE"),("HIGH","HIGH"),("CRITICAL","CRITICAL")], max_length=10)),
            ("risk_score", models.PositiveIntegerField(default=0)),
            ("latitude", models.FloatField()), ("longitude", models.FloatField()), ("radius_km", models.FloatField(default=10)),
            ("reason", models.TextField(blank=True)), ("rainfall", models.PositiveIntegerField(default=0)), ("soil_moisture", models.PositiveIntegerField(default=0)), ("ground_movement", models.PositiveIntegerField(default=0)), ("terrain", models.PositiveIntegerField(default=0)),
            ("active", models.BooleanField(default=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
        ], options={"ordering":["-risk_score","-updated_at"]}),
        migrations.CreateModel(name="Alert", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("hazard_type", models.CharField(max_length=40)), ("risk_level", models.CharField(max_length=10)), ("title", models.CharField(max_length=180)), ("message", models.TextField()), ("latitude", models.FloatField(blank=True, null=True)), ("longitude", models.FloatField(blank=True, null=True)),
            ("status", models.CharField(choices=[("NEW","NEW"),("READ","READ")], default="NEW", max_length=10)), ("created_at", models.DateTimeField(auto_now_add=True)), ("read_at", models.DateTimeField(blank=True, null=True)),
            ("risk_zone", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="alerts", to="core.riskzone")),
            ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="alerts", to="auth.user")),
        ], options={"ordering":["-created_at"]}),
    ]
