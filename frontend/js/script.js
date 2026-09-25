/* =========================================================
   SURAKSHA NER
   COMPLETE FRONTEND INTEGRATION
   ========================================================= */

const API_BASE =
    window.SURAKSHA_API_BASE ||
    "http://127.0.0.1:8000/api";


/* =========================================================
   HELPERS
   ========================================================= */

function toast(msg) {

    const t = document.createElement("div");

    t.className = "toast";
    t.textContent = msg;

    document.body.appendChild(t);

    setTimeout(
        () => t.classList.add("show"),
        20
    );

    setTimeout(() => {

        t.classList.remove("show");

        setTimeout(
            () => t.remove(),
            250
        );

    }, 2600);
}


function getToken() {

    return (
        localStorage.getItem("surakshaToken") || ""
    );
}


function getStoredUser() {

    try {

        return JSON.parse(
            localStorage.getItem(
                "surakshaUser"
            ) || "null"
        );

    } catch {

        return null;
    }
}


function authHeaders(extra = {}) {

    const headers = {

        "Content-Type":
            "application/json",

        ...extra
    };

    const token = getToken();

    if (token) {

        headers.Authorization =
            "Token " + token;
    }

    return headers;
}


async function api(path, options = {}) {

    const opts = {

        ...options,

        headers:
            authHeaders(
                options.headers || {}
            )
    };

    const response =
        await fetch(
            API_BASE + path,
            opts
        );

    let data = {};

    try {

        data =
            await response.json();

    } catch (_) {}


    if (!response.ok) {

        throw new Error(

            data.detail ||
            data.email ||
            data.password ||
            "Request failed"

        );
    }

    return data;
}


function initials(name = "User") {

    return (

        name
            .split(/\s+/)
            .filter(Boolean)
            .slice(0, 2)
            .map(x => x[0])
            .join("")
            .toUpperCase()

        || "U"
    );
}


function saveSession(data) {

    if (data.token) {

        localStorage.setItem(
            "surakshaToken",
            data.token
        );
    }

    if (data.user) {

        localStorage.setItem(
            "surakshaUser",
            JSON.stringify(data.user)
        );
    }
}


function clearSession() {

    localStorage.removeItem(
        "surakshaToken"
    );

    localStorage.removeItem(
        "surakshaUser"
    );
}


function requireLogin() {

    if (!getToken()) {

        location.href =
            "login.html";

        return false;
    }

    return true;
}


function riskClass(level) {

    return String(
        level || "LOW"
    ).toLowerCase();
}


function formatTime(value) {

    if (!value) return "—";

    return new Date(
        value
    ).toLocaleString(
        [],
        {
            hour: "2-digit",
            minute: "2-digit",
            day: "2-digit",
            month: "short"
        }
    );
}


function escapeHTML(value) {

    const div =
        document.createElement("div");

    div.textContent =
        value ?? "";

    return div.innerHTML;
}


/* =========================================================
   GENERIC DASHBOARD VALUE
   ========================================================= */

function setDashboardValue(id, value) {

    const element =
        document.getElementById(id);

    if (element) {

        element.textContent =
            value;
    }
}


/* =========================================================
   LOCATION
   ========================================================= */

function getBrowserLocation() {

    return new Promise(
        (resolve, reject) => {

            if (!navigator.geolocation) {

                reject(
                    new Error(
                        "Geolocation is not supported by this browser."
                    )
                );

                return;
            }

            navigator.geolocation
                .getCurrentPosition(

                    position => {

                        resolve({

                            latitude:
                                position.coords.latitude,

                            longitude:
                                position.coords.longitude

                        });
                    },

                    () => {

                        reject(

                            new Error(
                                "Location permission denied or unavailable."
                            )

                        );
                    },

                    {

                        enableHighAccuracy:
                            true,

                        timeout:
                            10000,

                        maximumAge:
                            0
                    }
                );
        }
    );
}


/* =========================================================
   REGISTER
   ========================================================= */

async function registerDemo(e) {

    e.preventDefault();

    const form =
        e.target;

    const name =
        form
            .querySelector(
                '[name="name"]'
            )
            .value
            .trim();

    const phone =
        form
            .querySelector(
                '[name="phone"]'
            )
            .value
            .trim();

    const email =
        form
            .querySelector(
                '[name="email"]'
            )
            .value
            .trim();

    const password =
        form
            .querySelector(
                '[name="password"]'
            )
            .value;

    const preferred_area =
        form
            .querySelector(
                '[name="preferred_area"]'
            )
            .value
            .trim();

    try {

        let location = null;

        try {

            location =
                await getBrowserLocation();

        } catch (_) {}


        const data =
            await api(
                "/auth/register/",
                {

                    method: "POST",

                    body:
                        JSON.stringify({

                            name,
                            phone,
                            email,
                            password,
                            preferred_area,

                            latitude:
                                location?.latitude
                                ?? null,

                            longitude:
                                location?.longitude
                                ?? null
                        })
                }
            );

        saveSession(data);

        toast(
            "Safety profile created!"
        );

        setTimeout(
            () =>
                location.href =
                    "dashboard.html",
            500
        );

    } catch (err) {

        toast(err.message);
    }
}


/* =========================================================
   LOGIN
   ========================================================= */

async function loginDemo(e) {

    e.preventDefault();

    const form =
        e.target;

    const email =
        form
            .querySelector(
                '[name="email"]'
            )
            .value
            .trim();

    const password =
        form
            .querySelector(
                '[name="password"]'
            )
            .value;

    try {

        const data =
            await api(
                "/auth/login/",
                {

                    method: "POST",

                    body:
                        JSON.stringify({

                            email,
                            password
                        })
                }
            );

        saveSession(data);

        toast(
            "Login successful!"
        );

        setTimeout(
            () => {

                location.href =
                    data.is_admin
                        ? "admin-dashboard.html"
                        : "dashboard.html";

            },
            400
        );

    } catch (err) {

        toast(err.message);
    }
}


/* =========================================================
   USER PROFILE
   ========================================================= */

async function loadMe() {

    if (!getToken())
        return null;

    try {

        const user =
            await api(
                "/auth/me/"
            );

        localStorage.setItem(
            "surakshaUser",
            JSON.stringify(user)
        );

        return user;

    } catch (err) {

        clearSession();

        return null;
    }
}


async function saveDemo() {

    if (!requireLogin())
        return;

    const name =
        document.querySelector(
            '[name="profile_name"]'
        )?.value;

    const phone =
        document.querySelector(
            '[name="profile_phone"]'
        )?.value;

    const preferred_area =
        document.querySelector(
            '[name="profile_area"]'
        )?.value;

    try {

        const data =
            await api(
                "/auth/me/",
                {

                    method: "PATCH",

                    body:
                        JSON.stringify({

                            name,
                            phone,
                            preferred_area
                        })
                }
            );

        localStorage.setItem(
            "surakshaUser",
            JSON.stringify(data)
        );

        toast(
            "Profile changes saved"
        );

    } catch (err) {

        toast(err.message);
    }
}


/* =========================================================
   LIVE LOCATION
   ========================================================= */

async function simulateLocation() {

    if (!requireLogin())
        return;

    try {

        toast(
            "Getting your current location..."
        );

        const position =
            await getBrowserLocation();

        const result =
            await api(
                "/location/",
                {

                    method: "POST",

                    body:
                        JSON.stringify({

                            latitude:
                                position.latitude,

                            longitude:
                                position.longitude
                        })
                }
            );

        if (
            result.new_alerts &&
            result.new_alerts.length
        ) {

            toast(
                "⚠️ New personalized risk alert created!"
            );

        } else {

            toast(
                "Location updated successfully!"
            );
        }

        await loadDashboard();

    } catch (error) {

        console.error(
            "Location update error:",
            error
        );

        toast(
            error.message ||
            "Unable to update location"
        );
    }
}


async function sendCurrentLocation() {

    await simulateLocation();

}


/* =========================================================
   WEATHER + AI + GIS
   ========================================================= */

function updateWeatherAIGIS(risk) {

    console.log("Updating Weather + AI + GIS:", risk);

    const live = risk.live_data || {};
    const ai = risk.ai_prediction || {};
    const matched = risk.matched_zone || {};
    const official = risk.official_alerts || {};


    /* =====================================================
       LIVE WEATHER
       ===================================================== */

    const rainfall =
        Number(live.rainfall_mm ?? 0);

    const humidity =
        Number(live.humidity_percent ?? 0);

    const temperature =
        live.temperature_c;

    const wind =
        live.wind_kmh;


    /* Rainfall */

    setDashboardValue(
        "liveRainfall",
        `${rainfall.toFixed(1)} mm`
    );

    setDashboardValue(
        "rainfallValue",
        `${rainfall.toFixed(1)} mm`
    );


    /* Humidity */

    setDashboardValue(
        "liveHumidity",
        `${humidity.toFixed(0)}%`
    );

    setDashboardValue(
        "humidityValue",
        `${humidity.toFixed(0)}%`
    );


    /* Temperature */

    if (temperature != null) {

        setDashboardValue(
            "liveTemperature",
            `${Number(temperature).toFixed(1)}°C`
        );

        setDashboardValue(
            "temperatureValue",
            `${Number(temperature).toFixed(1)}°C`
        );
    }


    /* Wind */

    if (wind != null) {

        setDashboardValue(
            "liveWind",
            `${Number(wind).toFixed(1)} km/h`
        );

        setDashboardValue(
            "windValue",
            `${Number(wind).toFixed(1)} km/h`
        );
    }


    /* =====================================================
       AI PREDICTION
       ===================================================== */

    const aiScore =
        ai.score != null
            ? Number(ai.score)
            : null;


    console.log(
        "AI SCORE:",
        aiScore
    );


    if (aiScore != null) {

        setDashboardValue(
            "aiPrediction",
            `${aiScore.toFixed(2)}/100`
        );

        setDashboardValue(
            "aiRiskValue",
            `${aiScore.toFixed(2)}/100`
        );
    }


    /* =====================================================
       WEATHER SCORE
       Same logic as backend weather engine
       ===================================================== */

    let rainfallScore = 0;

    if (rainfall >= 60) {

        rainfallScore = 100;

    } else if (rainfall >= 40) {

        rainfallScore = 80;

    } else if (rainfall >= 20) {

        rainfallScore = 60;

    } else if (rainfall >= 10) {

        rainfallScore = 40;

    } else if (rainfall > 0) {

        rainfallScore = 20;
    }


    let humidityScore = 0;

    if (humidity >= 90) {

        humidityScore = 100;

    } else if (humidity >= 80) {

        humidityScore = 70;

    } else if (humidity >= 70) {

        humidityScore = 40;
    }


    const calculatedWeatherScore =
        (
            rainfallScore * 0.75
        ) +
        (
            humidityScore * 0.25
        );


    console.log(
        "WEATHER SCORE:",
        calculatedWeatherScore
    );


    setDashboardValue(
        "weatherScore",
        `${Math.round(calculatedWeatherScore)}/100`
    );

    setDashboardValue(
        "weatherRiskValue",
        `${Math.round(calculatedWeatherScore)}/100`
    );


    /* =====================================================
       GIS ZONE
       ===================================================== */

    const zoneName =
        matched.name;


    setDashboardValue(
        "gisZone",
        zoneName ||
        "No active zone"
    );

    setDashboardValue(
        "zoneValue",
        zoneName ||
        "No active zone"
    );


    /* =====================================================
       GEOFENCE
       ===================================================== */

    let geofenceText = "—";


    if (
        matched.inside_polygon === true
    ) {

        geofenceText =
            "INSIDE";

    } else if (
        matched.inside_polygon === false
    ) {

        geofenceText =
            "OUTSIDE";

    } else if (
        matched.geofence_type
    ) {

        geofenceText =
            String(
                matched.geofence_type
            ).toUpperCase();
    }


    setDashboardValue(
        "geofenceValue",
        geofenceText
    );


    /* =====================================================
       DISTANCE
       ===================================================== */

    const distance =
        matched.distance_km;


    setDashboardValue(
        "distanceValue",
        distance != null
            ? `${Number(distance).toFixed(2)} km`
            : "—"
    );


    /* =====================================================
       OFFICIAL ALERT COUNT
       ===================================================== */

    setDashboardValue(
        "officialAlertCount",
        official.count != null
            ? official.count
            : 0
    );


    console.log(
        "✅ WEATHER + AI + GIS UPDATED",
        {
            rainfall,
            humidity,
            temperature,
            wind,
            aiScore,
            weatherScore:
                calculatedWeatherScore,
            gisZone:
                zoneName,
            geofence:
                geofenceText,
            distance
        }
    );
}

/* =========================================================
   MAIN DASHBOARD
   ========================================================= */

async function loadDashboard() {

    if (!getToken())
        return;

    try {

        const user =
            await loadMe();

        if (!user)
            return;


        /* -----------------------------------------------
           USER NAME
        ------------------------------------------------ */

        const heading =
            document.querySelector(
                ".page-head h1"
            );

        if (heading) {

            heading.textContent =
                "Good evening, " +
                (
                    user.name ||
                    "there"
                );
        }


        /* -----------------------------------------------
           AVATAR
        ------------------------------------------------ */

        const avatar =
            document.querySelector(
                ".avatar"
            );

        if (avatar) {

            avatar.textContent =
                initials(
                    user.name
                );
        }


        /* -----------------------------------------------
           LOCATION
        ------------------------------------------------ */

        const locationText =
            document.getElementById(
                "locationText"
            );

        if (
            locationText &&
            user.latitude != null &&
            user.longitude != null
        ) {

            locationText.textContent =
                `${Number(user.latitude).toFixed(4)}, ${Number(user.longitude).toFixed(4)}`;

        } else if (locationText) {

            locationText.textContent =
                "Location not available";
        }


        const locationAccess =
            document.getElementById(
                "locationAccess"
            );

        if (locationAccess) {

            locationAccess.textContent =
                user.location_enabled
                    ? "Enabled"
                    : "Not enabled";
        }


        const lastLocation =
            document.getElementById(
                "lastLocation"
            );

        if (lastLocation) {

            lastLocation.textContent =
                formatTime(
                    user.last_location_at
                );
        }


        /* -----------------------------------------------
           RISK ENGINE
        ------------------------------------------------ */

        if (
            user.latitude != null &&
            user.longitude != null
        ) {

            const risk =
                await api(

                    `/risk/current/?lat=${encodeURIComponent(user.latitude)}&lon=${encodeURIComponent(user.longitude)}`

                );


            /*
             * ONE RESPONSE DRIVES EVERYTHING
             */

            updateWeatherAIGIS(
                risk
            );

            updateRiskUI(
                risk
            );
        }


        /* -----------------------------------------------
           ALERTS
        ------------------------------------------------ */

        await loadDashboardAlerts();


        /* -----------------------------------------------
           OFFICIAL SACHET
        ------------------------------------------------ */

        await loadOfficialAlerts();


        /* -----------------------------------------------
           SAFETY STATUS
        ------------------------------------------------ */

        updateSafetyStatus(
            user
        );

    } catch (err) {

        console.error(
            "Dashboard error:",
            err
        );

        toast(
            err.message ||
            "Unable to load dashboard"
        );
    }
}


/* =========================================================
   UPDATE RISK UI
   ========================================================= */

function updateRiskUI(risk) {

    const score =
        Number(
            risk.risk_score || 0
        );

    const level =
        String(
            risk.risk_level || "LOW"
        ).toUpperCase();


    /* SCORE */

    setDashboardValue(
        "riskScore",
        score
    );


    /* METER */

    const meter =
        document.getElementById(
            "riskMeter"
        );

    if (meter) {

        meter.style.width =
            Math.min(
                100,
                score
            ) + "%";
    }


    /* PILL */

    const pill =
        document.getElementById(
            "riskPill"
        );

    if (pill) {

        pill.textContent =
            level;

        pill.className =
            "risk-pill " +
            riskClass(level);
    }


    /* BANNER */

    const banner =
        document.getElementById(
            "riskBanner"
        );

    if (banner) {

        if (
            level === "HIGH" ||
            level === "CRITICAL"
        ) {

            banner.style.display =
                "flex";

            const title =
                document.getElementById(
                    "bannerTitle"
                );

            if (title) {

                title.textContent =
                    `${level} risk conditions detected`;
            }


            const message =
                document.getElementById(
                    "bannerMessage"
                );

            if (message) {

                message.textContent =
                    risk.reason ||
                    "Hazard conditions detected near your location.";
            }

        } else {

            banner.style.display =
                "none";
        }
    }


    /* HAZARDS */

    updateHazards(
        risk.hazards || []
    );


    /* OFFICIAL ALERT COUNT */

    const official =
        risk.official_alerts || {};

    setDashboardValue(
        "officialAlertCount",
        official.count != null
            ? official.count
            : 0
    );
}


/* =========================================================
   HAZARDS
   ========================================================= */

function updateHazards(hazards) {

    const cards =
        document.querySelectorAll(
            ".hazard"
        );

    cards.forEach(
        card => {

            const type =
                (
                    card.dataset.hazard ||
                    card
                        .querySelector("b")
                        ?.textContent ||
                    ""
                )
                .toLowerCase();


            const match =
                hazards.find(
                    item =>
                        String(
                            item.hazard_type ||
                            ""
                        )
                        .toLowerCase()
                        .includes(type)
                );


            const strong =
                card.querySelector(
                    "strong"
                );


            const small =
                card.querySelector(
                    "small"
                );


            if (strong) {

                strong.textContent =
                    match
                        ? match.risk_level
                        : "LOW";
            }


            if (small) {

                small.textContent =
                    match
                        ? (
                            match.reason ||
                            "Active risk zone"
                        )
                        : "No active local warning";
            }

        }
    );
}


/* =========================================================
   DEMO LOCATION
   ========================================================= */

async function useDemoLocation() {

    if (!requireLogin())
        return;


    const demoLat =
        26.1445;

    const demoLon =
        91.7362;


    try {

        toast(
            "🧪 Loading Guwahati Demo..."
        );


        /*
         * IMPORTANT:
         * Use the same API that already works.
         */

        const risk =
            await api(
                `/risk/current/?lat=${demoLat}&lon=${demoLon}`
            );


        console.log(
            "DEMO RISK RESPONSE:",
            risk
        );


        /* -----------------------------------------------
           SAVE DEMO STATE
        ------------------------------------------------ */

        localStorage.setItem(
            "surakshaDemoLocation",
            JSON.stringify({

                latitude:
                    demoLat,

                longitude:
                    demoLon,

                name:
                    "Guwahati Demo Location"
            })
        );


        /* -----------------------------------------------
           LOCATION TEXT
        ------------------------------------------------ */

        const locationText =
            document.getElementById(
                "locationText"
            );

        if (locationText) {

            locationText.textContent =
                "Guwahati — Demo Location";
        }


        const locationAccess =
            document.getElementById(
                "locationAccess"
            );

        if (locationAccess) {

            locationAccess.textContent =
                "Demo Mode";
        }


        const lastLocation =
            document.getElementById(
                "lastLocation"
            );

        if (lastLocation) {

            lastLocation.textContent =
                "Demo location active";
        }


        /* -----------------------------------------------
           UPDATE COMPLETE RISK SYSTEM
        ------------------------------------------------ */

        updateWeatherAIGIS(
            risk
        );

        updateRiskUI(
            risk
        );


        /* -----------------------------------------------
           OFFICIAL ALERTS
        ------------------------------------------------ */

        await loadOfficialAlerts();


        /* -----------------------------------------------
           PERSONALIZED ALERTS
        ------------------------------------------------ */

        await loadDashboardAlerts();


        toast(
            "🧪 Guwahati Demo loaded successfully"
        );


    } catch (error) {

        console.error(
            "Demo location error:",
            error
        );

        toast(
            error.message ||
            "Unable to load demo location"
        );
    }
}


/* =========================================================
   DASHBOARD ALERTS
   ========================================================= */

async function loadDashboardAlerts() {

    const container =
        document.getElementById(
            "dashboardAlerts"
        );

    if (!container)
        return;


    try {

        const data =
            await api(
                "/alerts/"
            );

        const alerts =
            data.results || [];


        if (!alerts.length) {

            container.innerHTML = `

                <div class="alert-row">

                    🟢

                    <div>

                        <b>
                            No active alerts
                        </b>

                        <small>
                            No personalized warnings currently active.
                        </small>

                    </div>

                </div>

            `;

            return;
        }


        container.innerHTML =
            alerts
                .slice(0, 5)
                .map(
                    alert => {

                        const level =
                            riskClass(
                                alert.risk_level
                            );


                        let icon =
                            "🟢";


                        if (
                            level === "moderate"
                        )
                            icon = "🟠";


                        if (
                            level === "high"
                        )
                            icon = "🔴";


                        if (
                            level === "critical"
                        )
                            icon = "🚨";


                        return `

                            <div class="alert-row">

                                <span>
                                    ${icon}
                                </span>

                                <div>

                                    <b>
                                        ${escapeHTML(
                                            alert.title ||
                                            "Risk Alert"
                                        )}
                                    </b>

                                    <small>
                                        ${escapeHTML(
                                            alert.message ||
                                            ""
                                        )}
                                    </small>

                                    <small>
                                        ${formatTime(
                                            alert.created_at
                                        )}
                                    </small>

                                </div>

                            </div>

                        `;
                    }
                )
                .join("");


    } catch (err) {

        console.warn(
            "Dashboard alerts error:",
            err
        );
    }
}


/* =========================================================
   OFFICIAL SACHET / NDMA
   ========================================================= */

async function loadOfficialAlerts() {

    const container =
        document.getElementById(
            "officialAlertsList"
        );

    if (!container)
        return;


    try {

        container.innerHTML = `

            <p class="muted">
                Loading official SACHET alerts...
            </p>

        `;


        const live =
            await api(
                "/live-data/"
            );


        const official =
            live.official_alerts || {};


        if (!official.configured) {

            container.innerHTML = `

                <div class="official-empty">

                    <strong>
                        Official SACHET alerts are not configured.
                    </strong>

                </div>

            `;

            return;
        }


        const alerts =
            official.alerts || [];


        if (!alerts.length) {

            container.innerHTML = `

                <div class="official-empty">

                    <strong>
                        ✅ No active NER alerts
                    </strong>

                    <p>
                        No current SACHET / NDMA alert
                        matched the NER filter.
                    </p>

                </div>

            `;

            return;
        }


        container.innerHTML =
            alerts
                .slice(0, 5)
                .map(
                    alert => `

                        <div class="official-alert">

                            <div
                                class="official-alert-top"
                            >

                                <span
                                    class="risk-pill high"
                                >
                                    OFFICIAL
                                </span>

                                <small>
                                    SACHET / NDMA
                                </small>

                            </div>


                            <h3>
                                ${escapeHTML(
                                    alert.headline ||
                                    alert.event ||
                                    "Official Alert"
                                )}
                            </h3>


                            <p>
                                📍
                                ${escapeHTML(
                                    alert.ner_state ||
                                    alert.area ||
                                    "NER"
                                )}
                            </p>


                            <small>
                                🕐
                                ${escapeHTML(
                                    alert.effective ||
                                    "Time unavailable"
                                )}
                            </small>


                            ${
                                alert.link
                                ?
                                `

                                    <div
                                        class="official-link-wrap"
                                    >

                                        <a
                                            href="${escapeHTML(alert.link)}"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            View official SACHET alert →
                                        </a>

                                    </div>

                                `
                                :
                                ""
                            }

                        </div>

                    `
                )
                .join("");


    } catch (err) {

        console.warn(
            "SACHET error:",
            err
        );


        container.innerHTML = `

            <div class="official-empty">

                <strong>
                    Unable to load official alerts
                </strong>

                <p>
                    Please check the Django backend.
                </p>

            </div>

        `;
    }
}


/* =========================================================
   SAFETY STATUS
   ========================================================= */

function updateSafetyStatus(user) {

    const notification =
        document.getElementById(
            "notificationStatus"
        );


    if (notification) {

        notification.textContent =
            user.notifications_enabled
                ? "✓ Alert notifications enabled"
                : "⚠ Notifications disabled";
    }


    const location =
        document.getElementById(
            "locationStatus"
        );


    if (location) {

        location.textContent =
            user.location_enabled
                ? "✓ Location permission enabled"
                : "⚠ Location permission disabled";
    }


    const status =
        document.getElementById(
            "safetyStatus"
        );


    if (status) {

        status.textContent =
            user.notifications_enabled &&
            user.location_enabled

                ? "● Protected"

                : "● Setup required";
    }
}


/* =========================================================
   ALERT PAGE
   ========================================================= */

async function loadAlerts() {

    if (!requireLogin())
        return;


    try {

        const data =
            await api(
                "/alerts/"
            );


        const container =
            document.querySelector(
                ".alert-cards"
            );


        if (!container)
            return;


        container.innerHTML = "";


        const alerts =
            data.results || [];


        alerts.forEach(
            alert => {

                const element =
                    document.createElement(
                        "div"
                    );


                element.className =
                    "alert-card " +
                    riskClass(
                        alert.risk_level
                    );


                element.innerHTML = `

                    <a
                        href="alert-details.html?id=${alert.id}"
                    >

                        <div>

                            <span
                                class="risk-pill ${riskClass(alert.risk_level)}"
                            >
                                ${escapeHTML(
                                    alert.risk_level
                                )}
                            </span>


                            <h3>
                                ${escapeHTML(
                                    alert.title
                                )}
                            </h3>


                            <p>
                                ${escapeHTML(
                                    alert.message
                                )}
                            </p>


                            <small>
                                ${formatTime(
                                    alert.created_at
                                )}
                                ·
                                ${escapeHTML(
                                    alert.status
                                )}
                            </small>

                        </div>

                    </a>

                `;


                container.appendChild(
                    element
                );

            }
        );


        if (!alerts.length) {

            container.innerHTML = `

                <div class="card">

                    <h3>
                        No alerts
                    </h3>

                    <p class="muted">
                        No personalized alerts have
                        been generated yet.
                    </p>

                </div>

            `;
        }


    } catch (err) {

        toast(
            err.message
        );
    }
}


/* =========================================================
   MARK ALL READ
   ========================================================= */

async function markAllRead() {

    if (!requireLogin())
        return;


    try {

        const data =
            await api(
                "/alerts/"
            );


        for (
            const alert of
            data.results || []
        ) {

            if (
                alert.status ===
                "NEW"
            ) {

                await api(
                    `/alerts/${alert.id}/read/`,
                    {
                        method:
                            "POST"
                    }
                );
            }
        }


        toast(
            "All alerts marked as read"
        );


        await loadAlerts();


    } catch (err) {

        toast(
            err.message
        );
    }
}


/* =========================================================
   RISK MAP
   ========================================================= */

async function loadRiskMap() {

    try {

        const data =
            await api(
                "/risk-zones/"
            );


        const zones =
            data.results || [];


        const list =
            document.querySelector(
                ".legend-list"
            );


        if (!list)
            return;


        list.innerHTML = "";


        zones.forEach(
            zone => {

                let color =
                    "green";


                if (
                    zone.risk_level ===
                    "CRITICAL"
                ) {

                    color =
                        "red";

                } else if (
                    zone.risk_level ===
                    "HIGH"
                ) {

                    color =
                        "orange";

                } else if (
                    zone.risk_level ===
                    "MODERATE"
                ) {

                    color =
                        "yellow";
                }


                const element =
                    document.createElement(
                        "div"
                    );


                element.className =
                    "zone";


                element.innerHTML = `

                    <span
                        class="risk-dot ${color}"
                    >
                    </span>

                    <div>

                        <b>
                            ${escapeHTML(
                                zone.name
                            )}
                        </b>

                        <small>
                            ${escapeHTML(
                                zone.hazard_type
                            )}
                            ·
                            ${escapeHTML(
                                zone.risk_level
                            )}
                            ·
                            ${zone.risk_score}/100
                        </small>

                    </div>

                `;


                list.appendChild(
                    element
                );
            }
        );


    } catch (err) {

        console.warn(
            "Risk map error:",
            err
        );
    }
}


/* =========================================================
   PROFILE
   ========================================================= */

async function loadProfile() {

    if (!requireLogin())
        return;


    const user =
        await loadMe();


    if (!user)
        return;


    const name =
        document.querySelector(
            '[name="profile_name"]'
        );


    const phone =
        document.querySelector(
            '[name="profile_phone"]'
        );


    const email =
        document.querySelector(
            '[name="profile_email"]'
        );


    const area =
        document.querySelector(
            '[name="profile_area"]'
        );


    if (name)
        name.value =
            user.name || "";


    if (phone)
        phone.value =
            user.phone || "";


    if (email)
        email.value =
            user.email || "";


    if (area)
        area.value =
            user.preferred_area || "";


    const avatar =
        document.querySelector(
            ".avatar-lg"
        );


    if (avatar) {

        avatar.textContent =
            initials(
                user.name
            );
    }
}


/* =========================================================
   LANGUAGE
   ========================================================= */

function toggleLanguages() {

    const menu =
        document.getElementById(
            "languageMenu"
        );


    if (menu) {

        menu.classList.toggle(
            "show"
        );
    }
}


async function setLanguage(lang) {

    localStorage.setItem(
        "surakshaLanguage",
        lang
    );


    const button =
        document.querySelector(
            ".language-btn"
        );


    if (button) {

        button.innerHTML =
            "🌐 " + lang;
    }


    const menu =
        document.getElementById(
            "languageMenu"
        );


    if (menu) {

        menu.classList.remove(
            "show"
        );
    }


    if (getToken()) {

        try {

            await api(
                "/auth/me/",
                {

                    method: "PATCH",

                    body:
                        JSON.stringify({
                            language:
                                lang
                        })
                }
            );

        } catch (_) {}
    }


    toast(
        "Language selected: " +
        lang
    );
}


document.addEventListener(
    "click",
    event => {

        const wrapper =
            document.querySelector(
                ".language-wrap"
            );


        if (
            wrapper &&
            !wrapper.contains(
                event.target
            )
        ) {

            const menu =
                document.getElementById(
                    "languageMenu"
                );


            if (menu) {

                menu.classList.remove(
                    "show"
                );
            }
        }
    }
);


/* =========================================================
   ADMIN LOGIN
   ========================================================= */

async function demoAdminLogin(e) {

    e.preventDefault();


    try {

        const data =
            await api(
                "/auth/login/",
                {

                    method: "POST",

                    body:
                        JSON.stringify({

                            email:
                                "admin@suraksha.local",

                            password:
                                "Admin@12345"
                        })
                }
            );


        saveSession(data);


        location.href =
            "admin-dashboard.html";


    } catch (err) {

        toast(
            "Run the backend seed command first: " +
            err.message
        );
    }


    return false;
}


/* =========================================================
   ADMIN DASHBOARD
   ========================================================= */

async function loadAdmin() {

    if (!getToken()) {

        location.href =
            "login.html";

        return;
    }


    try {

        const me =
            await loadMe();


        if (!me)
            return;


        if (!me.is_staff) {

            toast(
                "Admin access required"
            );


            setTimeout(
                () =>
                    location.href =
                        "dashboard.html",
                500
            );


            return;
        }


        const summary =
            await api(
                "/admin/summary/"
            );


        const stats =
            document.querySelectorAll(
                ".stats .stat strong"
            );


        if (stats.length >= 4) {

            stats[0].textContent =
                summary.users;

            stats[1].textContent =
                summary.active_alerts;

            stats[2].textContent =
                summary.high_critical_zones;

            stats[3].textContent =
                summary.critical_zones;
        }


        const users =
            await api(
                "/admin/users/"
            );


        const tbody =
            document.querySelector(
                ".table-wrap tbody"
            );


        if (tbody) {

            tbody.innerHTML = "";


            (
                users.results || []
            ).forEach(
                user => {

                    const row =
                        document.createElement(
                            "tr"
                        );


                    row.innerHTML = `

                        <td>

                            <b>
                                ${escapeHTML(
                                    user.name
                                )}
                            </b>

                            <small>
                                ${escapeHTML(
                                    user.email
                                )}
                            </small>

                        </td>

                        <td>
                            ${escapeHTML(
                                user.preferred_area ||
                                "—"
                            )}
                        </td>

                        <td>
                            ${
                                user.location_enabled
                                    ? "Enabled"
                                    : "Limited"
                            }
                        </td>

                        <td>
                            All
                        </td>

                        <td>
                            ${formatTime(
                                user.last_location_at
                            )}
                        </td>

                    `;


                    tbody.appendChild(
                        row
                    );
                }
            );
        }


        const alerts =
            await api(
                "/admin/alerts/"
            );


        const alertBody =
            document.querySelector(
                "[data-admin-alerts] tbody"
            );


        if (alertBody) {

            alertBody.innerHTML = "";


            (
                alerts.results || []
            ).forEach(
                alert => {

                    const row =
                        document.createElement(
                            "tr"
                        );


                    row.innerHTML = `

                        <td>

                            <b>
                                ${escapeHTML(
                                    alert.title
                                )}
                            </b>

                            <small>
                                ${escapeHTML(
                                    alert.user_name
                                )}
                                ·
                                ${escapeHTML(
                                    alert.user_email
                                )}
                            </small>

                        </td>

                        <td>

                            <span
                                class="risk-pill ${riskClass(alert.risk_level)}"
                            >
                                ${escapeHTML(
                                    alert.risk_level
                                )}
                            </span>

                        </td>

                        <td>
                            ${escapeHTML(
                                alert.hazard_type
                            )}
                        </td>

                        <td>
                            ${formatTime(
                                alert.created_at
                            )}
                        </td>

                        <td>
                            ${escapeHTML(
                                alert.status
                            )}
                        </td>

                    `;


                    alertBody.appendChild(
                        row
                    );
                }
            );
        }


    } catch (err) {

        toast(
            err.message
        );
    }
}


async function loadAdminMap() {

    try {

        await loadRiskMap();

    } catch (_) {}
}


/* =========================================================
   PAGE INIT
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const path =
            location.pathname;


        if (
            path.endsWith(
                "/dashboard.html"
            )
        ) {

            loadDashboard();
        }


        if (
            path.endsWith(
                "/alerts.html"
            )
        ) {

            loadAlerts();
        }


        if (
            path.endsWith(
                "/map.html"
            )
        ) {

            loadRiskMap();
        }


        if (
            path.endsWith(
                "/profile.html"
            )
        ) {

            loadProfile();
        }


        if (
            path.includes(
                "admin-dashboard.html"
            )
            ||
            path.includes(
                "admin-users.html"
            )
            ||
            path.includes(
                "admin-alerts.html"
            )
        ) {

            loadAdmin();
        }


        if (
            path.includes(
                "admin-map.html"
            )
        ) {

            loadAdminMap();
        }

    }
);