# SURAKSHA NER — Complete Frontend + Django Backend

This ZIP contains your existing SURAKSHA NER frontend plus a beginner-friendly Django + Django REST Framework backend.

## What is implemented
- User registration and login with token authentication
- User profile and notification preferences
- Browser GPS location update
- SQLite database
- Risk zones for landslide, flood and very heavy rainfall
- Haversine distance based geofencing
- Current-risk API
- Automatic high/critical alert creation when a user location enters a risk zone
- User alert history and mark-as-read
- Django admin panel
- Admin summary, users, alerts and risk-zone management APIs
- Demo seed data so the project can be demonstrated without external weather APIs

## Important
This is a hackathon MVP, not a validated public-safety warning service. Demo risk zones are simulated. Real deployment should use authoritative disaster/weather data, validated models and authorized alert infrastructure.

## Windows setup
1. Install Python 3.12+ (Django 6.1 supports Python 3.12–3.14).
2. Open Command Prompt in the `backend` folder.
3. Run:

```bat
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```

4. Open the frontend with VS Code Live Server.
5. Open `frontend/index.html` using Live Server (for example `http://127.0.0.1:5500/NER-SAFE-Frontend/index.html`).

## Demo accounts
Admin: `admin@suraksha.local` / `Admin@12345`
User: `demo@suraksha.local` / `Demo@12345`

Change these passwords before any real deployment.

## Django admin
Open `http://127.0.0.1:8000/admin/` and sign in with the demo admin.

## API health
`http://127.0.0.1:8000/api/health/`

## Main API endpoints
- POST `/api/auth/register/`
- POST `/api/auth/login/`
- GET/PATCH `/api/auth/me/`
- POST `/api/location/`
- GET/POST `/api/risk-zones/`
- GET `/api/risk/current/?lat=26.1445&lon=91.7362`
- GET `/api/alerts/`
- POST `/api/alerts/<id>/read/`
- GET `/api/admin/summary/`
- GET `/api/admin/users/`
- GET `/api/admin/alerts/`

## Architecture
Frontend → Django REST API → SQLite → Risk Zones → Geofencing → Alerts → Admin dashboard.

The AI/ML and live weather/satellite/IoT integrations are intentionally separated so they can be added after the basic end-to-end flow works.


## Live data upgrade

The dashboard now calls `GET /api/live-data/?lat=<lat>&lon=<lon>` for live weather and official-feed status.

- **IMD:** configure `backend/.env` with `IMD_API_WEATHER_URL` and `IMD_API_TOKEN` after registering on the official IMD API Management portal. The exact product URL depends on the API product issued to your account.
- **SACHET / NDMA:** configure `SACHET_CAP_URL` with the CAP XML endpoint/identifier provided by SACHET for agency consumption.
- **Local demo fallback:** if IMD is not configured, the app uses Open-Meteo for current weather and clearly labels it as a non-government fallback. It never presents fallback weather as an official warning.

This first upgrade does **not** replace the existing risk-zone score with ML yet; it adds a real-data layer safely.
