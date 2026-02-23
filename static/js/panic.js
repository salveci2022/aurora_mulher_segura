document.addEventListener("DOMContentLoaded", function() {
    console.log("🌸 Aurora Mulher Segura - Sistema SOS iniciando...");

    const elements = {
        chips: document.querySelectorAll(".chip"),
        sos: document.getElementById("sosBtn"),
        status: document.getElementById("status"),
        name: document.getElementById("name"),
        message: document.getElementById("message")
    };

    if (!elements.sos || !elements.status) {
        console.error("❌ Erro crítico: Elementos necessários não encontrados!");
        return;
    }

    let selectedSituation = "";
    let holdTimer = null;
    let isHolding = false;

    function showStatus(message, type = "info") {
        if (!elements.status) return;
        
        elements.status.textContent = message;
        elements.status.className = "alert center";
        elements.status.classList.add(type === "success" ? "alert-ok" : type === "error" ? "alert-danger" : "alert-ok");
    }

    function clearStatus() {
        if (elements.status) {
            elements.status.textContent = "";
        }
    }

    if (elements.chips.length > 0) {
        elements.chips.forEach(chip => {
            chip.addEventListener("click", function(e) {
                e.preventDefault();
                
                elements.chips.forEach(c => c.classList.remove("active"));
                
                this.classList.add("active");
                
                let text = this.textContent.trim();
                selectedSituation = text;
                
                console.log("✅ Situação selecionada:", selectedSituation);
                showStatus(`✓ Situação: ${selectedSituation}`, "success");
                
                if (navigator.vibrate) navigator.vibrate(50);
            });
        });
    }

    async function getCurrentLocation() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject("GPS não suportado neste navegador");
                return;
            }

            console.log("📍 Solicitando permissão de localização...");
            showStatus("📍 Solicitando localização...", "info");

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    console.log("✅ Localização obtida:", position.coords);
                    
                    const location = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                        accuracy: Math.round(position.coords.accuracy),
                        timestamp: new Date().toISOString()
                    };
                    
                    if (location.accuracy < 50) {
                        showStatus(`📍 Localização precisa (${location.accuracy}m)`, "success");
                    } else {
                        showStatus(`📍 Localização aproximada (${location.accuracy}m)`, "info");
                    }
                    
                    resolve(location);
                },
                (error) => {
                    console.error("❌ Erro de GPS:", error);
                    
                    let errorMessage = "Erro ao obter localização";
                    switch(error.code) {
                        case 1:
                            errorMessage = "Permissão de GPS negada";
                            break;
                        case 2:
                            errorMessage = "Localização indisponível";
                            break;
                        case 3:
                            errorMessage = "Tempo de GPS esgotado";
                            break;
                    }
                    
                    showStatus(`⚠️ ${errorMessage}`, "info");
                    reject(errorMessage);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 15000,
                    maximumAge: 0
                }
            );
        });
    }

    async function sendSOSAlert() {
        try {
            console.log("🚨 INICIANDO ENVIO DE ALERTA SOS");
            
            if (!selectedSituation) {
                showStatus("⚠️ Selecione o tipo de situação", "error");
                if (navigator.vibrate) navigator.vibrate([100, 100, 100]);
                return false;
            }

            showStatus("⏳ Preparando alerta...", "info");
            if (elements.sos) {
                elements.sos.style.transform = "scale(0.95)";
            }

            const payload = {
                name: elements.name ? elements.name.value.trim() : "Usuária",
                situation: selectedSituation,
                message: elements.message ? elements.message.value.trim() : "",
                timestamp: new Date().toISOString()
            };

            console.log("📦 Payload base:", payload);

            try {
                showStatus("📍 Obtendo localização...", "info");
                const location = await getCurrentLocation();
                payload.lat = location.lat;
                payload.lng = location.lng;
                console.log("📍 Localização adicionada:", location);
            } catch (locationError) {
                console.warn("⚠️ Falha no GPS:", locationError);
                showStatus("⚠️ Enviando alerta sem localização", "info");
            }

            showStatus("📤 Enviando alerta...", "info");
            if (navigator.vibrate) navigator.vibrate(200);

            console.log("🌐 Enviando requisição para /api/send_alert");
            
            const response = await fetch("/api/send_alert", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify(payload)
            });

            console.log("📥 Resposta recebida:", response.status);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
            }

            const result = await response.json();
            console.log("📄 Resposta JSON:", result);

            if (result.ok) {
                showStatus("✅ ALERTA ENVIADO! Contatos notificados.", "success");
                
                if (elements.sos) {
                    elements.sos.style.background = "linear-gradient(145deg, #4caf50, #388e3c)";
                    setTimeout(() => {
                        elements.sos.style.background = "radial-gradient(circle at 50% 45%, rgba(255, 121, 218, 0.95), rgba(138, 36, 139, 0.65) 55%, rgba(40, 0, 60, 0.75))";
                        elements.sos.style.transform = "";
                    }, 1500);
                }
                
                if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
                
                return true;
            } else {
                throw new Error(result.message || "Erro desconhecido no servidor");
            }

        } catch (error) {
            console.error("❌ Erro crítico no envio:", error);
            
            showStatus(`❌ Erro: ${error.message || "Falha na comunicação"}`, "error");
            
            if (elements.sos) {
                elements.sos.style.background = "linear-gradient(145deg, #9c27b0, #7b1fa2)";
                setTimeout(() => {
                    elements.sos.style.background = "radial-gradient(circle at 50% 45%, rgba(255, 121, 218, 0.95), rgba(138, 36, 139, 0.65) 55%, rgba(40, 0, 60, 0.75))";
                }, 1000);
            }
            
            if (navigator.vibrate) navigator.vibrate(500);
            
            return false;
        }
    }

    function startHold(e) {
        e.preventDefault();
        
        if (isHolding) return;
        isHolding = true;
        
        console.log("👉 Hold iniciado");
        
        if (elements.sos) {
            elements.sos.classList.add("holding");
        }
        
        showStatus("⚠️ Segure por 1 segundo para enviar SOS", "info");
        if (navigator.vibrate) navigator.vibrate(50);

        holdTimer = setTimeout(() => {
            if (isHolding) {
                console.log("⏰ Hold completado - enviando alerta");
                sendSOSAlert();
            }
        }, 1000);
    }

    function cancelHold(e) {
        e.preventDefault();
        
        if (!isHolding) return;
        
        console.log("✋ Hold cancelado");
        
        if (holdTimer) {
            clearTimeout(holdTimer);
            holdTimer = null;
        }
        
        if (elements.sos) {
            elements.sos.classList.remove("holding");
        }
        
        if (elements.status && !elements.status.textContent.includes("✅")) {
            clearStatus();
        }
        
        isHolding = false;
    }

    if (elements.sos) {
        elements.sos.addEventListener("mousedown", startHold);
        elements.sos.addEventListener("mouseup", cancelHold);
        elements.sos.addEventListener("mouseleave", cancelHold);
        
        elements.sos.addEventListener("touchstart", startHold, { passive: false });
        elements.sos.addEventListener("touchend", cancelHold);
        elements.sos.addEventListener("touchcancel", cancelHold);
        
        elements.sos.addEventListener("contextmenu", (e) => e.preventDefault());
        
        elements.sos.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                startHold(e);
            }
        });
        
        elements.sos.addEventListener("keyup", (e) => {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                cancelHold(e);
            }
        });
        
        console.log("✅ Eventos do botão SOS configurados");
    }

    console.log("✅ Sistema Aurora inicializado com sucesso!");
    console.log("📊 Diagnóstico:", {
        chips: elements.chips.length,
        gps: !!navigator.geolocation,
        vibrate: !!navigator.vibrate,
        online: navigator.onLine,
        userAgent: navigator.userAgent
    });

    if (!navigator.onLine) {
        showStatus("⚠️ Modo offline - verifique sua internet", "info");
    } else {
        showStatus("✅ Sistema pronto - selecione uma situação", "success");
    }
});