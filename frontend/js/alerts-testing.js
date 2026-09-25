/*
 * SURAKSHA NER — Alert Testing Dashboard
 *
 * Frontend-only testing and mock SACHET/NDMA data.
 * No real API keys or external HTTP calls.
 */

(function (global) {
    "use strict";

    /** NER locations for the location dropdown. */
    const NER_LOCATIONS = [
        "Guwahati, Assam",
        "Dibrugarh, Assam",
        "Shillong, Meghalaya",
        "Imphal, Manipur",
        "Kohima, Nagaland",
        "Agartala, Tripura",
        "Aizawl, Mizoram",
        "Itanagar, Arunachal Pradesh",
        "Gangtok, Sikkim",
    ];

    /** Alert types supported on this testing page. */
    const ALERT_TYPES = ["Landslide", "Flood", "Heavy Rainfall"];

    /** Risk levels (stored uppercase internally). */
    const RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

    /** In-memory alert test history (cleared on reset). */
    let alertHistory = [];

    let nextHistoryId = 1;

    /** Default form values after reset. */
    const DEFAULT_FORM = {
        location: NER_LOCATIONS[0],
        riskLevel: "MEDIUM",
        alertType: "Heavy Rainfall",
        message: "",
    };

    /* =========================================================
       VALIDATION
       ========================================================= */

    function validateSeverity(riskLevel) {
        const level = String(riskLevel || "")
            .trim()
            .toUpperCase();
        return RISK_LEVELS.includes(level);
    }

    function validateLocation(location) {
        const text = String(location || "").trim();
        if (!text) {
            return { valid: false, error: "Select a location." };
        }
        return { valid: true };
    }

    function validateAlertType(type) {
        return ALERT_TYPES.includes(String(type || "").trim());
    }

    function validateMessage(message) {
        const text = String(message || "").trim();
        if (!text) {
            return { valid: false, error: "Alert message is required." };
        }
        if (text.length < 10) {
            return {
                valid: false,
                error: "Message should be at least 10 characters.",
            };
        }
        return { valid: true };
    }

    /**
     * Build a list of PASS/FAIL checks for the test status panel.
     */
    function runInputValidation(fields) {
        const checks = [];

        const loc = validateLocation(fields.location);
        checks.push({
            name: "Location selection",
            passed: loc.valid,
            detail: loc.valid ? fields.location : loc.error,
        });

        checks.push({
            name: "Risk level",
            passed: validateSeverity(fields.riskLevel),
            detail: fields.riskLevel,
        });

        checks.push({
            name: "Alert type",
            passed: validateAlertType(fields.alertType),
            detail: fields.alertType,
        });

        const msg = validateMessage(fields.message);
        checks.push({
            name: "Alert message",
            passed: msg.valid,
            detail: msg.valid ? "OK" : msg.error,
        });

        return checks;
    }

    function allChecksPassed(checks) {
        return checks.every(function (c) {
            return c.passed;
        });
    }

    /* =========================================================
       MOCK SACHET / NDMA (same shape as backend live_data)
       ========================================================= */

    /**
     * Simulates calling the official feed without network access.
     * Returns a Promise so the UI can show a short "loading" state.
     */
    function fetchMockSachetApi() {
        return new Promise(function (resolve) {
            setTimeout(function () {
                resolve({
                    configured: true,
                    provider: "SACHET / NDMA (mock demo)",
                    official: true,
                    mock: true,
                    count: 2,
                    total_india_alerts: 12,
                    filter: "NER states only",
                    ner_states: [
                        "Assam",
                        "Arunachal Pradesh",
                        "Meghalaya",
                        "Manipur",
                        "Mizoram",
                        "Nagaland",
                        "Tripura",
                        "Sikkim",
                    ],
                    feed_url: "(not used — demonstration only)",
                    message:
                        "Demo response mimicking backend official_alerts payload.",
                    alerts: [
                        {
                            event: "Heavy Rainfall",
                            headline:
                                "Heavy Rainfall Warning — Assam & Meghalaya",
                            description:
                                "IMD/SACHET-style demo: intense rainfall over NE India.",
                            area: "Assam, Meghalaya",
                            severity: "Severe",
                            urgency: "Immediate",
                            effective: "2026-09-25T08:00:00+05:30",
                            link: "",
                            ner_state: "Assam",
                        },
                        {
                            event: "Flood",
                            headline: "Flood Watch — Brahmaputra basin (demo)",
                            description:
                                "River levels being monitored; demo CAP-style entry.",
                            area: "Dibrugarh, Assam",
                            severity: "Moderate",
                            urgency: "Expected",
                            effective: "2026-09-24T14:30:00+05:30",
                            link: "",
                            ner_state: "Assam",
                        },
                    ],
                });
            }, 400);
        });
    }

    /** Match user location string to a NER state for SACHET comparison. */
    function nerStateFromLocation(location) {
        const text = String(location).toLowerCase();
        const map = [
            ["assam", "Assam"],
            ["meghalaya", "Meghalaya"],
            ["manipur", "Manipur"],
            ["nagaland", "Nagaland"],
            ["tripura", "Tripura"],
            ["mizoram", "Mizoram"],
            ["arunachal", "Arunachal Pradesh"],
            ["sikkim", "Sikkim"],
        ];
        for (let i = 0; i < map.length; i++) {
            if (text.indexOf(map[i][0]) !== -1) {
                return map[i][1];
            }
        }
        return null;
    }

    /**
     * Check if mock SACHET feed has an alert relevant to this test.
     */
    function compareWithMockSachet(generatedAlert, sachetPayload) {
        const state = nerStateFromLocation(generatedAlert.location);
        if (!state) {
            return {
                passed: false,
                detail: "Could not map location to a NER state.",
            };
        }

        const alerts = sachetPayload.alerts || [];
        const match = alerts.find(function (item) {
            const hay = (
                (item.area || "") +
                " " +
                (item.headline || "") +
                " " +
                (item.event || "")
            ).toLowerCase();
            return (
                hay.indexOf(state.toLowerCase()) !== -1 ||
                item.ner_state === state
            );
        });

        if (match) {
            return {
                passed: true,
                detail:
                    "Mock SACHET includes NER entry for " +
                    state +
                    ": " +
                    (match.headline || match.event),
            };
        }

        return {
            passed: false,
            detail:
                "No mock SACHET row matched " +
                state +
                " (demo still valid for local testing).",
        };
    }

    /* =========================================================
       ALERT GENERATION
       ========================================================= */

    function buildAlertFromForm(fields) {
        return {
            id: "test-" + String(nextHistoryId).padStart(4, "0"),
            location: fields.location.trim(),
            riskLevel: fields.riskLevel.toUpperCase(),
            alertType: fields.alertType,
            message: fields.message.trim(),
            status: "ACTIVE",
            timestamp: new Date().toISOString(),
            source: "SURAKSHA NER Test Console",
        };
    }

    function isEmergencyAlert(alert) {
        return alert.riskLevel === "CRITICAL";
    }

    function handleEmergencyAlert(alert) {
        if (!isEmergencyAlert(alert)) {
            return {
                isEmergency: false,
                message: "Standard test alert — no emergency escalation.",
            };
        }
        return {
            isEmergency: true,
            message:
                "CRITICAL level — mock emergency notify + SACHET cross-check recommended.",
        };
    }

    /**
     * Main TEST ALERT action: validate, preview, SACHET mock, history.
     */
    function testAlert(fields) {
        const validation = runInputValidation(fields);
        if (!allChecksPassed(validation)) {
            return {
                ok: false,
                validation: validation,
                overall: "FAIL",
            };
        }

        const alert = buildAlertFromForm(fields);
        nextHistoryId += 1;
        alertHistory.unshift(alert);

        const emergency = handleEmergencyAlert(alert);
        validation.push({
            name: "Emergency handling",
            passed: true,
            detail: emergency.message,
        });

        return {
            ok: true,
            alert: alert,
            validation: validation,
            overall: "PASS",
            emergency: emergency,
        };
    }

    function clearHistory() {
        alertHistory = [];
        nextHistoryId = 1;
    }

    function formatTimestamp(iso) {
        try {
            return new Date(iso).toLocaleString("en-IN", {
                dateStyle: "medium",
                timeStyle: "short",
            });
        } catch (_) {
            return iso;
        }
    }

    function riskCssClass(level) {
        const map = {
            LOW: "low",
            MEDIUM: "medium",
            HIGH: "high",
            CRITICAL: "critical",
        };
        return map[String(level).toUpperCase()] || "low";
    }

    function escapeHtml(text) {
        return String(text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    /* =========================================================
       AUTOMATED SUITE (optional — Run All Tests button)
       ========================================================= */

    function assert(name, condition, detail) {
        return {
            name: name,
            passed: Boolean(condition),
            detail: detail || "",
        };
    }

    function runAllTests() {
        const results = [];

        const good = testAlert({
            location: NER_LOCATIONS[0],
            riskLevel: "HIGH",
            alertType: "Flood",
            message: "Automated test message for flood scenario.",
        });
        results.push(
            assert(
                "Alert creation via TEST ALERT",
                good.ok && good.alert,
                good.ok ? good.alert.id : "validation failed"
            )
        );

        results.push(
            assert(
                "Severity validation",
                validateSeverity("CRITICAL") && !validateSeverity("EXTREME"),
                "CRITICAL ok"
            )
        );

        results.push(
            assert(
                "Location validation",
                validateLocation(NER_LOCATIONS[2]).valid,
                NER_LOCATIONS[2]
            )
        );

        const filtered = alertHistory.filter(function (a) {
            return a.alertType === "Flood";
        });
        results.push(
            assert(
                "Alert history records type",
                filtered.length >= 1,
                filtered.length + " Flood row(s)"
            )
        );

        results.push(
            assert(
                "Alert status ACTIVE",
                good.alert && good.alert.status === "ACTIVE",
                "ACTIVE"
            )
        );

        const emerg = handleEmergencyAlert({
            riskLevel: "CRITICAL",
        });
        results.push(
            assert(
                "Emergency alert handling",
                emerg.isEmergency,
                emerg.message
            )
        );

        return {
            results: results,
            summary: {
                total: results.length,
                passed: results.filter(function (r) {
                    return r.passed;
                }).length,
                failed: results.filter(function (r) {
                    return !r.passed;
                }).length,
            },
        };
    }

    /* =========================================================
       UI
       ========================================================= */

    function renderValidationPanel(container, checks, overall) {
        if (!container) {
            return;
        }

        if (!checks || !checks.length) {
            container.innerHTML =
                '<p class="empty-note">Run TEST ALERT to see validation results.</p>';
            return;
        }

        const badge =
            overall === "PASS"
                ? '<span class="overall pass">PASS</span>'
                : '<span class="overall fail">FAIL</span>';

        container.innerHTML =
            '<div class="overall-row">Overall: ' +
            badge +
            "</div>" +
            checks
                .map(function (item) {
                    return (
                        '<div class="test-row">' +
                        "<span>" +
                        escapeHtml(item.name) +
                        (item.detail
                            ? " — " + escapeHtml(item.detail)
                            : "") +
                        "</span>" +
                        '<span class="' +
                        (item.passed ? "pass" : "fail") +
                        '">' +
                        (item.passed ? "PASS" : "FAIL") +
                        "</span>" +
                        "</div>"
                    );
                })
                .join("");
    }

    function renderPreview(container, alert, emergency) {
        if (!container) {
            return;
        }
        if (!alert) {
            container.innerHTML =
                '<p class="empty-note">Generated alert preview will appear here.</p>';
            return;
        }

        const sev = riskCssClass(alert.riskLevel);
        container.innerHTML =
            '<div class="preview-card ' +
            sev +
            '">' +
            '<div class="preview-top">' +
            '<span class="risk-pill ' +
            sev +
            '">' +
            escapeHtml(alert.riskLevel) +
            "</span>" +
            '<span class="type-pill">' +
            escapeHtml(alert.alertType) +
            "</span>" +
            (emergency && emergency.isEmergency
                ? '<span class="emergency-tag">EMERGENCY</span>'
                : "") +
            "</div>" +
            "<h3>" +
            escapeHtml(alert.message) +
            "</h3>" +
            '<p class="preview-meta">' +
            "<strong>Location:</strong> " +
            escapeHtml(alert.location) +
            "<br><strong>Time:</strong> " +
            escapeHtml(formatTimestamp(alert.timestamp)) +
            "<br><strong>Status:</strong> " +
            escapeHtml(alert.status) +
            "<br><strong>ID:</strong> " +
            escapeHtml(alert.id) +
            "</p>" +
            "</div>";
    }

    function renderHistoryTable(tbody) {
        if (!tbody) {
            return;
        }

        if (!alertHistory.length) {
            tbody.innerHTML =
                '<tr><td colspan="6" class="empty-cell">No test alerts yet. Use TEST ALERT above.</td></tr>';
            return;
        }

        tbody.innerHTML = alertHistory
            .map(function (row) {
                return (
                    "<tr>" +
                    "<td>" +
                    escapeHtml(row.id) +
                    "</td>" +
                    "<td>" +
                    escapeHtml(row.location) +
                    "</td>" +
                    "<td>" +
                    escapeHtml(row.alertType) +
                    "</td>" +
                    '<td><span class="risk-pill ' +
                    riskCssClass(row.riskLevel) +
                    '">' +
                    escapeHtml(row.riskLevel) +
                    "</span></td>" +
                    "<td>" +
                    escapeHtml(row.status) +
                    "</td>" +
                    "<td>" +
                    escapeHtml(formatTimestamp(row.timestamp)) +
                    "</td>" +
                    "</tr>"
                );
            })
            .join("");
    }

    function renderSachetMock(container, payload, integrationCheck) {
        if (!container || !payload) {
            return;
        }

        const alertsHtml = (payload.alerts || [])
            .map(function (a) {
                return (
                    '<div class="official-alert mock-official">' +
                    '<div class="official-alert-top">' +
                    '<span class="risk-pill high">OFFICIAL (MOCK)</span>' +
                    "<small>SACHET / NDMA</small>" +
                    "</div>" +
                    "<h3>" +
                    escapeHtml(a.headline || a.event) +
                    "</h3>" +
                    "<p>📍 " +
                    escapeHtml(a.ner_state || a.area || "NER") +
                    "</p>" +
                    "<small>🕐 " +
                    escapeHtml(a.effective || "—") +
                    "</small>" +
                    "</div>"
                );
            })
            .join("");

        const integrationRow = integrationCheck
            ? '<p class="sachet-check ' +
              (integrationCheck.passed ? "ok" : "warn") +
              '"><strong>Integration check:</strong> ' +
              escapeHtml(integrationCheck.detail) +
              "</p>"
            : "";

        container.innerHTML =
            '<p class="mock-note">' +
            escapeHtml(payload.message || "") +
            " · Provider: " +
            escapeHtml(payload.provider) +
            " · NER count: " +
            escapeHtml(String(payload.count)) +
            "</p>" +
            integrationRow +
            alertsHtml +
            '<details class="json-details"><summary>Raw mock JSON</summary><pre>' +
            escapeHtml(JSON.stringify(payload, null, 2)) +
            "</pre></details>";
    }

    function getFormValues() {
        return {
            location: document.getElementById("inputLocation").value,
            riskLevel: document.getElementById("inputRisk").value,
            alertType: document.getElementById("inputType").value,
            message: document.getElementById("inputMessage").value,
        };
    }

    function setFormValues(values) {
        document.getElementById("inputLocation").value =
            values.location || DEFAULT_FORM.location;
        document.getElementById("inputRisk").value =
            values.riskLevel || DEFAULT_FORM.riskLevel;
        document.getElementById("inputType").value =
            values.alertType || DEFAULT_FORM.alertType;
        document.getElementById("inputMessage").value =
            values.message != null ? values.message : DEFAULT_FORM.message;
    }

    function resetDashboard(clearTable) {
        setFormValues(DEFAULT_FORM);

        renderPreview(
            document.getElementById("alertPreview"),
            null,
            null
        );
        renderValidationPanel(
            document.getElementById("testStatus"),
            null,
            null
        );

        const sachetEl = document.getElementById("sachetMockPanel");
        if (sachetEl) {
            sachetEl.innerHTML =
                '<p class="empty-note">Mock SACHET/NDMA response loads when you run TEST ALERT.</p>';
        }

        if (clearTable) {
            clearHistory();
        }
        renderHistoryTable(document.getElementById("historyBody"));
    }

    function populateLocationSelect() {
        const select = document.getElementById("inputLocation");
        if (!select || select.options.length) {
            return;
        }
        NER_LOCATIONS.forEach(function (loc) {
            const opt = document.createElement("option");
            opt.value = loc;
            opt.textContent = loc;
            select.appendChild(opt);
        });
    }

    function bindAlertsTestingPage() {
        populateLocationSelect();

        const testBtn = document.getElementById("testAlertBtn");
        const resetBtn = document.getElementById("resetBtn");
        const runAllBtn = document.getElementById("runAllTestsBtn");
        const previewEl = document.getElementById("alertPreview");
        const statusEl = document.getElementById("testStatus");
        const historyBody = document.getElementById("historyBody");
        const sachetEl = document.getElementById("sachetMockPanel");
        const summaryEl = document.getElementById("autoTestSummary");
        const autoResultsEl = document.getElementById("autoTestResults");

        setFormValues(DEFAULT_FORM);
        renderHistoryTable(historyBody);

        if (testBtn) {
            testBtn.addEventListener("click", function () {
                testBtn.disabled = true;
                testBtn.textContent = "Testing…";

                const fields = getFormValues();
                const result = testAlert(fields);

                renderValidationPanel(
                    statusEl,
                    result.validation,
                    result.overall
                );

                if (result.ok) {
                    renderPreview(
                        previewEl,
                        result.alert,
                        result.emergency
                    );
                    renderHistoryTable(historyBody);

                    sachetEl.innerHTML =
                        '<p class="empty-note">Loading mock SACHET/NDMA…</p>';

                    fetchMockSachetApi().then(function (payload) {
                        const check = compareWithMockSachet(
                            result.alert,
                            payload
                        );
                        renderSachetMock(sachetEl, payload, check);
                        testBtn.disabled = false;
                        testBtn.textContent = "TEST ALERT";
                    });
                } else {
                    renderPreview(previewEl, null, null);
                    testBtn.disabled = false;
                    testBtn.textContent = "TEST ALERT";
                }
            });
        }

        if (resetBtn) {
            resetBtn.addEventListener("click", function () {
                resetDashboard(true);
            });
        }

        if (runAllBtn && autoResultsEl) {
            runAllBtn.addEventListener("click", function () {
                const run = runAllTests();
                autoResultsEl.innerHTML = run.results
                    .map(function (item) {
                        return (
                            '<div class="test-row">' +
                            "<span>" +
                            escapeHtml(item.name) +
                            "</span>" +
                            '<span class="' +
                            (item.passed ? "pass" : "fail") +
                            '">' +
                            (item.passed ? "PASS" : "FAIL") +
                            "</span>" +
                            "</div>"
                        );
                    })
                    .join("");
                if (summaryEl) {
                    summaryEl.textContent =
                        run.summary.total +
                        " tests · " +
                        run.summary.passed +
                        " passed · " +
                        run.summary.failed +
                        " failed";
                }
                renderHistoryTable(historyBody);
            });
        }
    }

    const api = {
        NER_LOCATIONS: NER_LOCATIONS,
        ALERT_TYPES: ALERT_TYPES,
        RISK_LEVELS: RISK_LEVELS,
        validateSeverity: validateSeverity,
        validateLocation: validateLocation,
        fetchMockSachetApi: fetchMockSachetApi,
        testAlert: testAlert,
        runAllTests: runAllTests,
        clearHistory: clearHistory,
        getHistory: function () {
            return alertHistory.slice();
        },
    };

    global.SurakshaAlertsTesting = api;

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bindAlertsTestingPage);
    } else {
        bindAlertsTestingPage();
    }
})(window);
