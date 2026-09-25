"""Live-data adapters for SURAKSHA NER.

The project can use official IMD/SACHET endpoints when credentials/URLs are
configured. For a zero-key local demo, weather falls back to Open-Meteo so the
UI still receives real current weather data. The fallback is explicitly marked
as non-government data in the API response.
"""

import json
import os
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

load_dotenv()
from django.core.cache import cache
from datetime import datetime, timezone as dt_timezone

NER_STATES = (
    "assam", "arunachal pradesh", "meghalaya", "manipur", "mizoram",
    "nagaland", "tripura", "sikkim"
)


def _get_json(url, headers=None, timeout=10):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "SURAKSHA-NER/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_text(url, headers=None, timeout=10):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "SURAKSHA-NER/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _get_cap_xml_with_etag(url):
    """Fetch SACHET CAP XML using the ETag/304 pattern required by SACHET."""
    cache_key = "suraksha_sachet_cap_cache"
    etag_key = "suraksha_sachet_cap_etag"
    cached_xml = cache.get(cache_key)
    old_etag = cache.get(etag_key)
    headers = {"User-Agent": "SURAKSHA-NER/1.0"}
    if old_etag:
        headers["If-None-Match"] = old_etag

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml = response.read().decode("utf-8", errors="replace")
            new_etag = response.headers.get("ETag")
            cache.set(cache_key, xml, 300)
            if new_etag:
                cache.set(etag_key, new_etag, 300)
            return xml
    except urllib.error.HTTPError as exc:
        if exc.code == 304 and cached_xml:
            return cached_xml
        raise


def _imd_weather(lat, lon):
    """Use a configured IMD endpoint.

    IMD's current API platform requires account/API access. Because the exact
    product endpoint depends on the API product selected by the account, this
    adapter intentionally takes IMD_API_WEATHER_URL from the environment.
    The URL may contain {lat} and {lon} placeholders.
    """
    url = os.getenv("IMD_API_WEATHER_URL", "").strip()
    token = os.getenv("IMD_API_TOKEN", "").strip()
    if not url:
        raise RuntimeError("IMD_API_WEATHER_URL is not configured")

    url = url.format(lat=lat, lon=lon)
    headers = {"User-Agent": "SURAKSHA-NER/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = _get_json(url, headers=headers)
    # Keep normalization deliberately tolerant because IMD API products have
    # different field names. Raw data is also returned for hackathon debugging.
    current = data.get("current", data) if isinstance(data, dict) else {}
    rain = current.get("rainfall", current.get("rain", current.get("precipitation")))
    temp = current.get("temperature", current.get("temp"))
    humidity = current.get("humidity", current.get("relative_humidity"))
    wind = current.get("wind_speed", current.get("windSpeed"))
    return {
        "provider": "IMD",
        "official": True,
        "temperature_c": temp,
        "humidity_percent": humidity,
        "rainfall_mm": rain,
        "wind_kmh": wind,
        "raw": data,
    }


def _open_meteo_weather(lat, lon):
    params = urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m",
        "timezone": "Asia/Kolkata",
    })
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    data = _get_json(url)
    current = data.get("current", {})
    return {
        "provider": "Open-Meteo",
        "official": False,
        "temperature_c": current.get("temperature_2m"),
        "humidity_percent": current.get("relative_humidity_2m"),
        "rainfall_mm": current.get("rain"),
        "precipitation_mm": current.get("precipitation"),
        "wind_kmh": current.get("wind_speed_10m"),
        "observed_at": current.get("time"),
        "raw": data,
    }


def get_live_weather(lat, lon):
    try:
        if os.getenv("IMD_API_WEATHER_URL", "").strip():
            return _imd_weather(lat, lon)
    except Exception as exc:
        return {"provider": "IMD", "official": True, "available": False,
                "error": str(exc), "fallback": _safe_open_meteo(lat, lon)}
    return _safe_open_meteo(lat, lon)


def _safe_open_meteo(lat, lon):
    try:
        result = _open_meteo_weather(lat, lon)
        result["available"] = True
        return result
    except Exception as exc:
        return {"provider": "Open-Meteo", "official": False, "available": False,
                "error": str(exc)}


def _local_name(tag):
    return tag.rsplit("}", 1)[-1].lower()


def _xml_value(element, names):
    wanted = {n.lower() for n in names}
    for child in element.iter():
        if _local_name(child.tag) in wanted and child.text:
            return child.text.strip()
    return ""


def get_sachet_alerts():
    """
    Read the SACHET / NDMA India CAP RSS feed and keep only
    alerts relevant to the North Eastern Region (NER).

    NER states:
    Assam, Arunachal Pradesh, Meghalaya, Manipur,
    Mizoram, Nagaland, Tripura and Sikkim.
    """

    url = os.getenv("SACHET_CAP_URL", "").strip()

    if not url:
        return {
            "configured": False,
            "provider": "SACHET / NDMA",
            "official": True,
            "alerts": [],
            "count": 0,
            "message": (
                "Configure SACHET_CAP_URL from the official "
                "SACHET RSS feed to enable live government alerts."
            ),
        }

    # -----------------------------------------
    # NER STATE KEYWORDS
    # -----------------------------------------

    ner_states = {
        "assam",
        "arunachal pradesh",
        "meghalaya",
        "manipur",
        "mizoram",
        "nagaland",
        "tripura",
        "sikkim",
    }

    try:
        # -----------------------------------------
        # GET RSS FEED
        # -----------------------------------------

        xml_text = _get_text(url)

        root = ET.fromstring(xml_text)

        all_alerts = []
        ner_alerts = []

        # -----------------------------------------
        # READ RSS ITEMS
        # -----------------------------------------

        for item in root.iter():
            if _local_name(item.tag) != "item":
                continue

            title = _xml_value(
                item,
                ["title", "headline"]
            )

            description = _xml_value(
                item,
                ["description"]
            )

            area = _xml_value(
                item,
                ["area", "areadesc", "areaDesc"]
            )

            event = _xml_value(
                item,
                ["event"]
            )

            pub_date = _xml_value(
                item,
                ["pubDate", "effective"]
            )

            link = _xml_value(
                item,
                ["link"]
            )

            # -----------------------------------------
            # COMBINE TEXT FOR NER SEARCH
            # -----------------------------------------

            searchable_text = " ".join([
                title,
                description,
                area,
                event,
            ]).lower()

            # -----------------------------------------
            # CHECK NER STATE
            # -----------------------------------------

            matched_state = None

            for state in ner_states:
                if state in searchable_text:
                    matched_state = state.title()
                    break

            alert = {
                "event": event,
                "headline": title,
                "description": description,
                "area": area,
                "severity": "",
                "urgency": "",
                "effective": pub_date,
                "link": link,
                "ner_state": matched_state,
            }

            all_alerts.append(alert)

            if matched_state:
                ner_alerts.append(alert)

        # -----------------------------------------
        # RETURN ONLY NER ALERTS
        # -----------------------------------------

        return {
            "configured": True,
            "provider": "SACHET / NDMA",
            "official": True,
            "alerts": ner_alerts,
            "count": len(ner_alerts),
            "total_india_alerts": len(all_alerts),
            "filter": "NER states only",
            "ner_states": [
                "Assam",
                "Arunachal Pradesh",
                "Meghalaya",
                "Manipur",
                "Mizoram",
                "Nagaland",
                "Tripura",
                "Sikkim",
            ],
            "feed_url": url,
        }

    except Exception as exc:

        return {
            "configured": True,
            "provider": "SACHET / NDMA",
            "official": True,
            "alerts": [],
            "count": 0,
            "error": str(exc),
            "feed_url": url,
        }


def get_live_data(lat, lon):
    weather = get_live_weather(lat, lon)
    sachet = get_sachet_alerts()
    return {
        "timestamp": datetime.now(dt_timezone.utc).isoformat(),
        "location": {"latitude": lat, "longitude": lon},
        "weather": weather,
        "official_alerts": sachet,
        "data_status": "LIVE" if weather.get("available", True) else "DEGRADED",
    }
