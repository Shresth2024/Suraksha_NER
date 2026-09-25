from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Profile, RiskZone

class Command(BaseCommand):
    help = "Create demo admin/user and Northeast risk zones."
    def handle(self, *args, **kwargs):
        admin_email="admin@suraksha.local"
        admin, created=User.objects.get_or_create(username=admin_email, defaults={"email":admin_email,"first_name":"SURAKSHA","last_name":"Admin","is_staff":True,"is_superuser":True})
        admin.is_staff=True; admin.is_superuser=True; admin.set_password("Admin@12345"); admin.save()
        Profile.objects.get_or_create(user=admin)
        user_email="demo@suraksha.local"
        user, created=User.objects.get_or_create(username=user_email, defaults={"email":user_email,"first_name":"Demo","last_name":"User"})
        user.set_password("Demo@12345"); user.save()
        Profile.objects.update_or_create(user=user, defaults={"phone":"+91 9000000000","preferred_area":"Guwahati, Assam","latitude":26.1445,"longitude":91.7362,"location_enabled":True})
        zones=[
            {"name":"Guwahati Rainfall Zone","hazard_type":"Very Heavy Rainfall","risk_level":"HIGH","risk_score":68,"latitude":26.1445,"longitude":91.7362,"radius_km":15,"reason":"Heavy rainfall may increase local flood and landslide risk."},
            {"name":"Assam Flood Watch Zone","hazard_type":"Flood","risk_level":"MODERATE","risk_score":46,"latitude":26.2,"longitude":91.8,"radius_km":25,"reason":"Prototype flood-risk zone based on simulated rainfall and river conditions."},
            {"name":"Sikkim Landslide Zone","hazard_type":"Landslide","risk_level":"CRITICAL","risk_score":88,"latitude":27.3389,"longitude":88.6065,"radius_km":18,"reason":"Heavy rainfall + steep terrain can increase slope instability. Prototype data for demonstration."},
            {"name":"Meghalaya Landslide Zone","hazard_type":"Landslide","risk_level":"HIGH","risk_score":72,"latitude":25.5788,"longitude":91.8933,"radius_km":20,"reason":"Prototype high-risk zone representing intense rainfall and vulnerable slopes."},
        ]
        for item in zones:
            RiskZone.objects.update_or_create(name=item["name"], defaults=item)
        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("Admin: admin@suraksha.local / Admin@12345")
        self.stdout.write("User:  demo@suraksha.local / Demo@12345")
