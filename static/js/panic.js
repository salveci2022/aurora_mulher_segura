(function() {
    "use strict";
    console.log("🌸 Aurora - GPS Alta Precisão iniciando...");

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    function init() {
        const elements = {
            chips: document.querySelectorAll(".chip"),
            sos: document.getElementById("sosBtn"),
            status: document.getElementById("statusMsg"),
            name: document.getElementById("nomeInput"),
            message: document.getElementById("mensagemInput"),
            gpsStatus: document.getElementById("gpsStatus")
        };

        if (!elements.sos) {
            console.error("❌ Botão SOS não encontrado!");
            return;
        }

        let selectedSituation = "Assédio";
        let holdTimer = null;
        let isHolding = false;
        let lastLocation = null;
        let gpsAccuracy = 999;
        let gpsReadings = 0;

        function initHighAccuracyGPS() {
            if (!navigator.geolocation) {
                updateGPSStatus('error', 'GPS não suportado');
                return;
            }

            const highAccuracyOptions = {
                enableHighAccuracy: true,
                timeout: 30000,
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

                    if (acc <= 10) {
                        updateGPSStatus('excellent', `±${acc}m (EXCELENTE)`);
                        gpsAccuracy = acc;
                    } else if (acc <= 25) {
                        updateGPSStatus('good', `±${acc}m (BOM)`);
                        gpsAccuracy = acc;
                    } else {
                        updateGPSStatus('warning', `±${acc}m (RUIM)`);
                    }

                    console.log(`✅ GPS ${gpsReadings}ª leitura:`, lastLocation);
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
                        lastLocation = {
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

        function updateGPSStatus(quality, text) {
            if (elements.gpsStatus) {
                const colors = {
                    'excellent': '#4caf50',
                    'good': '#8bc34a',
                    'warning': '#ff9800',
                    'error': '#f44336'
                };
                elements.gpsStatus.innerHTML = `<span style="color: ${colors[quality]}">●</span> ${text}`;
                elements.gpsStatus.style.color = colors[quality];
            }
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

                if (gpsAccuracy > 50 && gpsReadings < 3) {
                    showStatus("📍 Aguardando GPS mais preciso...", "info");
                    await new Promise(resolve => setTimeout(resolve, 3000));
                }

                if (lastLocation) {
                    payload.lat = lastLocation.lat;
                    payload.lng = lastLocation.lng;
                    payload.accuracy = lastLocation.accuracy;
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
    }
})();