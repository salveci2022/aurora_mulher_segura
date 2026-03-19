// Sistema SOS Aurora Mulher Segura v3.1
document.addEventListener("DOMContentLoaded", function () {
    console.log("🌸 Aurora — Sistema SOS iniciando...");

    const elements = {
        chips: document.querySelectorAll(".chip"),
        sos: document.getElementById("sosBtn"),
        status: document.getElementById("status"),
        name: document.getElementById("name"),
        message: document.getElementById("message"),
        shareLocation: document.getElementById("shareLocation"),
        // FIX: Target the wrapper div and the inner span separately
        gpsStatusBox: document.getElementById("gpsStatus"),
        gpsStatusText: document.getElementById("gpsText")
    };

    if (!elements.sos || !elements.status) {
        console.error("❌ Elementos essenciais não encontrados!");
        return;
    }

    let selectedSituation = "Assédio"; // FIX: Default matches the pre-selected chip
    let holdTimer = null;
    let isHolding = false;
    let currentLocation = null;

    function showStatus(msg, type = "info") {
        if (!elements.status) return;
        elements.status.textContent = msg;
        elements.status.className = "alert center";
        if (type === "success") elements.status.classList.add("alert-ok");
        else if (type === "error") elements.status.classList.add("alert-danger");
    }

    // FIX: Update GPS status without clobbering the inner <span>
    function showGpsStatus(msg, state = "") {
        const box = elements.gpsStatusBox;
        const txt = elements.gpsStatusText;
        if (!box) return;
        box.classList.add("active");
        box.className = "gps-status active" + (state ? " " + state : "");
        if (txt) txt.textContent = msg;
    }

    // Chips
    elements.chips.forEach(chip => {
        chip.addEventListener("click", function (e) {
            e.preventDefault();
            elements.chips.forEach(c => c.classList.remove("active"));
            this.classList.add("active");
            selectedSituation = this.dataset.value || this.textContent.trim();
            showStatus(`✓ Situação: ${selectedSituation}`, "success");
        });
    });

    // GPS
    async function getCurrentLocation() {
        if (!elements.shareLocation || !elements.shareLocation.checked) {
            console.log("⚠️ Localização não autorizada");
            return null;
        }

        if (!navigator.geolocation) {
            console.error("❌ GPS não suportado");
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

            console.log("✅ Localização obtida:", currentLocation);
            showGpsStatus(`GPS obtido ±${currentLocation.accuracy}m`, "good");
            return currentLocation;

        } catch (error) {
            console.error("❌ Erro GPS:", error);
            showGpsStatus("Erro ao capturar GPS", "poor");
            return null;
        }
    }

    // Enviar alerta
    async function sendSOSAlert() {
        try {
            if (!selectedSituation) {
                showStatus("⚠️ Selecione a situação", "error");
                return false;
            }

            showStatus("⏳ Preparando alerta...", "info");

            const location = await getCurrentLocation();

            // Pega client_id da URL (?c=...) ou do campo hidden
            const urlParams = new URLSearchParams(window.location.search);
            const clientId = urlParams.get('c') ||
                             (document.getElementById('clientId') ? document.getElementById('clientId').value : null);

            const payload = {
                name: elements.name ? (elements.name.value.trim() || "Usuária") : "Usuária",
                situation: selectedSituation,
                message: elements.message ? elements.message.value.trim() : "",
                location: location,
                client_id: clientId,
                timestamp: new Date().toISOString()
            };

            console.log("📤 Enviando:", payload);
            showStatus("📤 Enviando...", "info");

            const response = await fetch("/api/send_alert", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();
            console.log("✅ Enviado:", result);
            showStatus("✅ ALERTA ENVIADO COM SUCESSO!", "success");

            if (elements.sos) {
                elements.sos.classList.add("sent");
                setTimeout(() => elements.sos.classList.remove("sent"), 3000);
            }

            return true;

        } catch (error) {
            console.error("❌ Erro:", error);
            showStatus(`❌ Erro ao enviar: ${error.message}`, "error");
            return false;
        }
    }

    // Hold detection
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

        if (holdTimer) {
            clearTimeout(holdTimer);
            holdTimer = null;
        }

        if (elements.sos) elements.sos.classList.remove("holding");
        isHolding = false;

        // Only reset status if alert was not successfully sent
        if (elements.status && !elements.status.textContent.includes("✅")) {
            showStatus("🌸 Sistema pronto", "info");
        }
    }

    // Events — mouse + touch
    if (elements.sos) {
        elements.sos.addEventListener("mousedown", startHold);
        elements.sos.addEventListener("mouseup", cancelHold);
        elements.sos.addEventListener("mouseleave", cancelHold);
        elements.sos.addEventListener("touchstart", startHold, { passive: false });
        elements.sos.addEventListener("touchend", cancelHold);
        elements.sos.addEventListener("touchcancel", cancelHold);
    }

    console.log("✅ Aurora SOS — Sistema pronto!");
});
