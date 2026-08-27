// Sistema SOS Aurora Mulher Segura v4.1
document.addEventListener("DOMContentLoaded", function () {
    const elements = {
        chips: document.querySelectorAll(".chip"),
        sos: document.getElementById("sosBtn"),
        status: document.getElementById("status"),
        name: document.getElementById("name"),
        message: document.getElementById("message"),
        shareLocation: document.getElementById("shareLocation"),
        gpsStatusBox: document.getElementById("gpsStatus"),
        gpsStatusText: document.getElementById("gpsText"),
        clientIdDisplay: document.getElementById("clientIdDisplay"),
        clientIdInput: document.getElementById("clientIdInput"),
        saveClientIdBtn: document.getElementById("saveClientIdBtn"),
        clearClientIdBtn: document.getElementById("clearClientIdBtn"),
        configSection: document.getElementById("configSection")
    };

    if (!elements.sos || !elements.status) return;

    let selectedSituation = "Assédio";
    let holdTimer = null;
    let isHolding = false;
    let currentLocation = null;

    // ==========================================
    // CLIENT ID — localStorage
    // ==========================================
    function getClientId() {
        return localStorage.getItem("aurora_client_id") || null;
    }

    function updateClientIdUI() {
        const cid = getClientId();
        if (elements.clientIdDisplay) {
            if (cid) {
                elements.clientIdDisplay.textContent = "✅ ID configurado: " + cid;
                elements.clientIdDisplay.style.color = "#4caf50";
            } else {
                elements.clientIdDisplay.textContent = "⚠️ ID não configurado — alertas não chegarão às suas pessoas de confiança!";
                elements.clientIdDisplay.style.color = "#ff9800";
            }
        }
    }

    if (elements.saveClientIdBtn) {
        elements.saveClientIdBtn.addEventListener("click", function () {
            const val = (elements.clientIdInput?.value || "").trim();
            if (!val) {
                alert("⚠️ Digite o ID fornecido pelo administrador.");
                return;
            }
            localStorage.setItem("aurora_client_id", val);
            updateClientIdUI();
            if (elements.configSection) elements.configSection.classList.remove("open");
            showStatus("✅ ID salvo! Alertas serão enviados para suas pessoas de confiança.", "success");
        });
    }

    if (elements.clearClientIdBtn) {
        elements.clearClientIdBtn.addEventListener("click", function () {
            if (confirm("Remover ID configurado?")) {
                localStorage.removeItem("aurora_client_id");
                if (elements.clientIdInput) elements.clientIdInput.value = "";
                updateClientIdUI();
            }
        });
    }

    // Show current ID in input on open
    const toggleConfigBtn = document.getElementById("toggleConfigBtn");
    if (toggleConfigBtn && elements.configSection) {
        toggleConfigBtn.addEventListener("click", function () {
            elements.configSection.classList.toggle("open");
            if (elements.clientIdInput && elements.configSection.classList.contains("open")) {
                elements.clientIdInput.value = getClientId() || "";
                elements.clientIdInput.focus();
            }
        });
    }

    updateClientIdUI();

    // ==========================================
    // STATUS / GPS
    // ==========================================
    function showStatus(msg, type = "info") {
        if (!elements.status) return;
        elements.status.textContent = msg;
        elements.status.className = "alert center";
        if (type === "success") elements.status.classList.add("alert-ok");
        else if (type === "error") elements.status.classList.add("alert-danger");
    }

    function showGpsStatus(msg, state = "") {
        const box = elements.gpsStatusBox;
        const txt = elements.gpsStatusText;
        if (!box) return;
        box.classList.add("active");
        box.className = "gps-status active" + (state ? " " + state : "");
        if (txt) txt.textContent = msg;
    }

    // ==========================================
    // CHIPS
    // ==========================================
    elements.chips.forEach(chip => {
        chip.addEventListener("click", function (e) {
            e.preventDefault();
            elements.chips.forEach(c => c.classList.remove("active"));
            this.classList.add("active");
            selectedSituation = this.dataset.value || this.textContent.trim();
            showStatus("✓ Situação: " + selectedSituation, "success");
        });
    });

    // ==========================================
    // GPS
    // ==========================================
    async function getCurrentLocation() {
        if (!elements.shareLocation || !elements.shareLocation.checked) return null;
        if (!navigator.geolocation) {
            showGpsStatus("GPS não suportado neste dispositivo", "poor");
            return null;
        }

        try {
            showGpsStatus("Obtendo localização...");
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                });
            });

            currentLocation = {
                lat: position.coords.latitude,
                lng: position.coords.longitude,
                accuracy: Math.round(position.coords.accuracy)
            };

            showGpsStatus("GPS obtido ±" + currentLocation.accuracy + "m", "good");
            return currentLocation;
        } catch (error) {
            showGpsStatus("Erro ao capturar GPS", "poor");
            return null;
        }
    }

    // ==========================================
    // ENVIAR ALERTA
    // ==========================================
    async function sendSOSAlert() {
        try {
            if (!selectedSituation) {
                showStatus("⚠️ Selecione a situação", "error");
                return false;
            }

            showStatus("⏳ Preparando alerta...", "info");

            const location = await getCurrentLocation();
            const clientId = getClientId();

            const payload = {
                name: elements.name ? (elements.name.value.trim() || "Usuária") : "Usuária",
                situation: selectedSituation,
                message: elements.message ? elements.message.value.trim() : "",
                location: location,
                client_id: clientId,
                timestamp: new Date().toISOString()
            };

            showStatus("📤 Enviando...", "info");

            const response = await fetch("/api/send_alert", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error("HTTP " + response.status);

            const result = await response.json();

            if (!clientId) {
                showStatus("⚠️ Alerta enviado, mas sem ID configurado! Suas pessoas de confiança podem não receber.", "error");
            } else {
                showStatus("✅ ALERTA ENVIADO COM SUCESSO!", "success");
            }

            if (elements.sos) {
                elements.sos.classList.add("sent");
                setTimeout(() => elements.sos.classList.remove("sent"), 3000);
            }

            return true;

        } catch (error) {
            showStatus("❌ Erro ao enviar: " + error.message, "error");
            return false;
        }
    }

    // ==========================================
    // HOLD DETECTION
    // ==========================================
    function startHold(e) {
        e.preventDefault();
        if (isHolding) return;
        isHolding = true;
        if (elements.sos) elements.sos.classList.add("holding");
        showStatus("⚠️ Segure por 1 segundo...", "info");
        holdTimer = setTimeout(() => {
            if (isHolding) sendSOSAlert();
        }, 1000);
    }

    function cancelHold(e) {
        e.preventDefault();
        if (!isHolding) return;
        if (holdTimer) { clearTimeout(holdTimer); holdTimer = null; }
        if (elements.sos) elements.sos.classList.remove("holding");
        isHolding = false;
        if (elements.status && !elements.status.textContent.includes("✅") && !elements.status.textContent.includes("⚠️ Alerta")) {
            showStatus("🌸 Sistema pronto", "info");
        }
    }

    if (elements.sos) {
        elements.sos.addEventListener("mousedown", startHold);
        elements.sos.addEventListener("mouseup", cancelHold);
        elements.sos.addEventListener("mouseleave", cancelHold);
        elements.sos.addEventListener("touchstart", startHold, { passive: false });
        elements.sos.addEventListener("touchend", cancelHold);
        elements.sos.addEventListener("touchcancel", cancelHold);
    }
});
