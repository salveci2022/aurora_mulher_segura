// Sistema SOS Aurora Mulher Segura
document.addEventListener("DOMContentLoaded", function() {
    console.log("🌸 Aurora - Sistema SOS iniciando...");
    
    const elements = {
        chips: document.querySelectorAll(".chip"),
        sos: document.getElementById("sosBtn"),
        status: document.getElementById("status"),
        name: document.getElementById("name"),
        message: document.getElementById("message"),
        shareLocation: document.getElementById("shareLocation"),
        gpsStatus: document.getElementById("gpsStatus")
    };

    if (!elements.sos || !elements.status) {
        console.error("❌ Elementos não encontrados!");
        return;
    }

    let selectedSituation = "";
    let holdTimer = null;
    let isHolding = false;
    let currentLocation = null;

    function showStatus(message, type = "info") {
        if (!elements.status) return;
        elements.status.textContent = message;
        elements.status.className = "alert center";
        if (type === "success") elements.status.classList.add("alert-ok");
        else if (type === "error") elements.status.classList.add("alert-danger");
    }

    // Sistema de chips
    elements.chips.forEach(chip => {
        chip.addEventListener("click", function(e) {
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
            if (elements.gpsStatus) {
                elements.gpsStatus.textContent = "❌ GPS não suportado";
                elements.gpsStatus.className = "alert alert-danger";
            }
            return null;
        }

        try {
            console.log("📍 Solicitando localização...");
            if (elements.gpsStatus) {
                elements.gpsStatus.textContent = "📍 Obtendo localização...";
                elements.gpsStatus.className = "alert";
            }

            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(
                    resolve,
                    reject,
                    {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 0
                    }
                );
            });

            currentLocation = {
                lat: position.coords.latitude,
                lng: position.coords.longitude,
                accuracy: Math.round(position.coords.accuracy)
            };

            console.log("✅ Localização obtida:", currentLocation);
            
            if (elements.gpsStatus) {
                elements.gpsStatus.textContent = `✅ GPS: ±${currentLocation.accuracy}m`;
                elements.gpsStatus.className = "alert alert-ok";
            }

            return currentLocation;
        } catch (error) {
            console.error("❌ Erro GPS:", error);
            if (elements.gpsStatus) {
                elements.gpsStatus.textContent = "❌ Erro ao capturar GPS";
                elements.gpsStatus.className = "alert alert-danger";
            }
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

            // Obter localização
            const location = await getCurrentLocation();

            const payload = {
                name: elements.name ? elements.name.value.trim() : "Usuária",
                situation: selectedSituation,
                message: elements.message ? elements.message.value.trim() : "",
                location: location,
                timestamp: new Date().toISOString()
            };

            console.log("📤 Enviando alerta:", payload);
            showStatus("📤 Enviando...", "info");

            const response = await fetch("/api/send_alert", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            console.log("✅ Alerta enviado:", result);

            showStatus("✅ ALERTA ENVIADO!", "success");
            
            // Feedback visual
            if (elements.sos) {
                elements.sos.style.background = "linear-gradient(145deg, #4caf50, #388e3c)";
                setTimeout(() => {
                    elements.sos.style.background = "";
                }, 2000);
            }

            return true;
        } catch (error) {
            console.error("❌ Erro:", error);
            showStatus(`❌ Erro: ${error.message}`, "error");
            return false;
        }
    }

    // Sistema de hold (segurar botão)
    function startHold(e) {
        e.preventDefault();
        if (isHolding) return;
        
        isHolding = true;
        if (elements.sos) {
            elements.sos.classList.add("holding");
        }
        
        showStatus("⚠️ Segure por 1 segundo...", "info");
        
        holdTimer = setTimeout(() => {
            if (isHolding) {
                sendSOSAlert();
            }
        }, 1000);
    }

    function cancelHold(e) {
        e.preventDefault();
        if (!isHolding) return;
        
        if (holdTimer) {
            clearTimeout(holdTimer);
            holdTimer = null;
        }
        
        if (elements.sos) {
            elements.sos.classList.remove("holding");
        }
        
        isHolding = false;
        
        if (!elements.status.textContent.includes("✅")) {
            showStatus("", "info");
        }
    }

    // Event listeners do SOS
    if (elements.sos) {
        elements.sos.addEventListener("mousedown", startHold);
        elements.sos.addEventListener("mouseup", cancelHold);
        elements.sos.addEventListener("mouseleave", cancelHold);
        elements.sos.addEventListener("touchstart", startHold, { passive: false });
        elements.sos.addEventListener("touchend", cancelHold);
    }

    console.log("✅ Sistema Aurora inicializado!");
});