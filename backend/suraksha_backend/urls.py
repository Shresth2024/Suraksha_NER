from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", views.health),
    path("api/auth/register/", views.RegisterView.as_view()),
    path("api/auth/login/", views.LoginView.as_view()),
    path("api/auth/me/", views.MeView.as_view()),
    path("api/location/", views.LocationUpdateView.as_view()),
    path("api/live-data/", views.LiveDataView.as_view()),
    path("api/risk-zones/", views.RiskZoneListCreateView.as_view()),
    path("api/risk-zones/<int:pk>/", views.RiskZoneDetailView.as_view()),
    path("api/risk/current/", views.CurrentRiskView.as_view()),
    path("api/alerts/", views.AlertListView.as_view()),
    path("api/alerts/<int:pk>/read/", views.AlertReadView.as_view()),
    path("api/admin/summary/", views.AdminSummaryView.as_view()),
    path("api/admin/users/", views.AdminUsersView.as_view()),
    path("api/admin/alerts/", views.AdminAlertsView.as_view()),
]
