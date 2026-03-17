// Sistema SOS Aurora Mulher Segura
document.addEventListener("DOMContentLoaded", function() {
    console.log("🌸 Aurora Mulher Segura - Sistema SOS iniciando...");
    
    const elements = {
        chips: document.querySelectorAll(".chip"),
        sos: document.getElementById("sosBtn"),
        status: document.getElementById("status"),
        name: document.getElementById("name"),
        message: document.getElementById("message"),
        gpsStatus: document.getElementById("gpsStatus")
    };

    if (!elements.sos || !elements.status) {
        console.error("❌ Erro crítico: Elementos não encontrados!");
        return;
    }

    let selectedSituation = "Assédio";
    let holdTimer = null;
    let isHolding = false;
    let lastLocation = null;
    let gpsAccuracy = 999;
    let gpsReadings = 0;
    let bestLocation = null;

    function initHighAccuracyGPS() {
        if (!navigator.geolocation) {
            updateGPSStatus('error', 'GPS não suportado');
            return;
        }

        const highAccuracyOptions = {
            enableHighAccuracy: true,
            timeout: 60000,
            maximumAge: 0
        };

        navigator.geolocation.getCurrentPosition(
            (position) => {
                gpsReadings++;
                const acc = Math.round(position.coords.accuracy);
                
                lastLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                    accuracy: acc
                };

                if (acc < gpsAccuracy || !bestLocation) {
                    bestLocation = lastLocation;
                    gpsAccuracy = acc;
                }

                updateGPSStatus(gpsAccuracy, gpsReadings);
            },
            (error) => {
                updateGPSStatus('error', 'Erro GPS');
            },
            highAccuracyOptions
        );

        navigator.geolocation.watchPosition(
            (position) => {
                gpsReadings++;
                const acc = Math.round(position.coords.accuracy);
                
                if (acc < gpsAccuracy) {
                    bestLocation = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                        accuracy: acc
                    };
                    gpsAccuracy = acc;
                }
            },
            null,
            highAccuracyOptions
        );
    }

    function updateGPSStatus(accuracy, readings) {
        if (!elements.gpsStatus) return;
        
        let color, icon, text;
        
        if (accuracy <= 10) {
            color = '#4caf50'; icon = '🟢'; text = 'EXCELENTE';
        } else if (accuracy <= 25) {
            color = '#8bc34a'; icon = '🟡'; text = 'BOM';
        } else if (accuracy <= 50) {
            color = '#ff9800'; icon = '🟠'; text = 'MÉDIO';
        } else {
            color = '#f44336'; icon = '🔴'; text = 'RUIM';
        }

        elements.gpsStatus.innerHTML = `<span style="color: ${color}">${icon} GPS: ±${accuracy}m (${text}) - ${readings} leituras</span>`;
        elements.gpsStatus.style.color = color;
    }

    initHighAccuracyGPS();

    if (elements.chips.length > 0) {
        elements.chips.forEach(chip => {
            chip.addEventListener("click", function(e) {
                e.preventDefault();
                elements.chips.forEach(c => c.classList.remove("active"));
                this.classList.add("active");
                selectedSituation = this.dataset.value || this.textContent.trim();
                showStatus(`✓ Situação: ${selectedSituation}`, "success");
                if (navigator.vibrate) navigator.vibrate(50);
            });
        });
    }

    function showStatus(message, type = "info") {
        if (!elements.status) return;
        elements.status.textContent = message;
        elements.status.className = "alert center";
        if (type === "success") elements.status.classList.add("alert-ok");
        else if (type === "error") elements.status.classList.add("alert-danger");
    }

    async function sendSOSAlert() {
        try {
            if (!selectedSituation) {
                showStatus("⚠️ Selecione o tipo de situação", "error");
                return false;
            }

            showStatus("⏳ Preparando alerta...", "info");

            const payload = {
                name: elements.name ? elements.name.value.trim() : "Usuária",
                situation: selectedSituation,
                message: elements.message ? elements.message.value.trim() : "",
                timestamp: new Date().toISOString()
            };

            if (bestLocation) {
                payload.lat = bestLocation.lat;
                payload.lng = bestLocation.lng;
                payload.accuracy = bestLocation.accuracy;
                payload.gps_readings = gpsReadings;
            }

            showStatus("📤 Enviando alerta...", "info");

            const response = await fetch("/api/send_alert", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (result && result.ok) {
                showStatus("✅ ALERTA ENVIADO!", "success");
                if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
                return true;
            } else {
                throw new Error("Erro no servidor");
            }

        } catch (error) {
            showStatus(`❌ Erro: ${error.message}`, "error");
            return false;
        }
    }

    function startHold(e) {
        e.preventDefault();
        if (isHolding) return;
        isHolding = true;
        if (elements.sos) elements.sos.classList.add("holding");
        showStatus("⚠️ Segure por 1 segundo...", "info");
        if (navigator.vibrate) navigator.vibrate(50);
        holdTimer = setTimeout(() => {
            if (isHolding) sendSOSAlert();
        }, 1000);
    }

    function cancelHold(e) {
        e.preventDefault();
        if (!isHolding) return;
        if (holdTimer) clearTimeout(holdTimer);
        if (elements.sos) elements.sos.classList.remove("holding");
        isHolding = false;
    }

    if (elements.sos) {
        elements.sos.addEventListener("mousedown", startHold);
        elements.sos.addEventListener("mouseup", cancelHold);
        elements.sos.addEventListener("mouseleave", cancelHold);
        elements.sos.addEventListener("touchstart", startHold, { passive: false });
        elements.sos.addEventListener("touchend", cancelHold);
    }

    console.log("✅ Sistema Aurora inicializado!");
});