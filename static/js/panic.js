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
        gpsStatus: document.getElementById("gpsStatus"),
        gpsText: document.getElementById("gpsText")
    };

    if (!elements.sos || !elements.status) {
        console.error("❌ Elementos não encontrados!");
        return;
    }

    let selectedSituation = "";
    let holdTimer = null;
    let isHolding = false;
    let currentLocation = null;
    let watchId = null;
    let permissionRequested = false;

    function showStatus(message, type = "info") {
        if (!elements.status) return;
        elements.status.textContent = message;
        elements.status.className = "alert center";
        if (type === "success") {
            elements.status.classList.add("alert-ok");
            elements.status.classList.remove("alert-danger");
        } else if (type === "error") {
            elements.status.classList.add("alert-danger");
            elements.status.classList.remove("alert-ok");
        } else {
            elements.status.classList.remove("alert-ok", "alert-danger");
        }
    }

    // Chips
    elements.chips.forEach(chip => {
        chip.addEventListener("click", function(e) {
            e.preventDefault();
            elements.chips.forEach(c => c.classList.remove("active"));
            this.classList.add("active");
            selectedSituation = this.dataset.value || this.textContent.trim();
            showStatus(`✓ Situação: ${selectedSituation}`, "success");
        });
    });

    // 🔥 FUNÇÃO PARA SOLICITAR PERMISSÃO EXPLICITAMENTE
    async function requestLocationPermission() {
        if (!navigator.permissions || !navigator.permissions.query) {
            console.log("⚠️ API de permissão não suportada");
            return true; // Tenta mesmo assim
        }

        try {
            const permission = await navigator.permissions.query({ name: 'geolocation' });
            console.log("📌 Status da permissão:", permission.state);
            
            if (permission.state === 'granted') {
                return true;
            } else if (permission.state === 'prompt') {
                showStatus("📍 Por favor, permita o acesso à localização", "info");
                return true; // Vai pedir na hora do getCurrentPosition
            } else {
                updateGPSStatus("❌ Permissão negada - ative nas configurações", "poor");
                return false;
            }
        } catch (error) {
            console.log("Erro ao verificar permissão:", error);
            return true;
        }
    }

    function updateGPSStatus(message, type = "info") {
        if (!elements.gpsStatus || !elements.gpsText) return;
        
        elements.gpsStatus.style.display = "block";
        elements.gpsText.textContent = message;
        
        elements.gpsStatus.classList.remove("good", "poor", "active");
        
        if (type === "good") {
            elements.gpsStatus.classList.add("good", "active");
        } else if (type === "poor") {
            elements.gpsStatus.classList.add("poor", "active");
        } else if (type === "info") {
            elements.gpsStatus.classList.add("active");
        }
    }

    async function startWatchingLocation() {
        if (!navigator.geolocation) {
            updateGPSStatus("❌ GPS não suportado neste dispositivo", "poor");
            return;
        }

        // Verifica permissão primeiro
        const hasPermission = await requestLocationPermission();
        if (!hasPermission) {
            return;
        }

        // Para watch anterior se existir
        if (watchId) {
            navigator.geolocation.clearWatch(watchId);
        }

        updateGPSStatus("📍 Solicitando permissão de localização...", "info");

        // Primeiro tenta getCurrentPosition para pedir permissão
        navigator.geolocation.getCurrentPosition(
            // Sucesso - permissão concedida
            (position) => {
                console.log("✅ Permissão concedida!");
                
                // Agora inicia o watch
                watchId = navigator.geolocation.watchPosition(
                    // Sucesso do watch
                    (pos) => {
                        currentLocation = {
                            lat: pos.coords.latitude,
                            lng: pos.coords.longitude,
                            accuracy: Math.round(pos.coords.accuracy)
                        };
                        
                        console.log("📍 GPS atualizado:", currentLocation);
                        
                        if (currentLocation.accuracy < 50) {
                            updateGPSStatus(`✅ GPS ativo: ±${currentLocation.accuracy}m`, "good");
                        } else {
                            updateGPSStatus(`⚠️ GPS aproximado: ±${currentLocation.accuracy}m`, "poor");
                        }
                    },
                    // Erro do watch
                    (error) => {
                        console.error("❌ Erro no watch GPS:", error);
                        handleGPSError(error);
                    },
                    {
                        enableHighAccuracy: true,
                        maximumAge: 0,
                        timeout: 10000
                    }
                );
            },
            // Erro - permissão negada
            (error) => {
                console.error("❌ Erro ao solicitar permissão:", error);
                handleGPSError(error);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    }

    function handleGPSError(error) {
        let errorMsg = "Erro no GPS";
        switch(error.code) {
            case error.PERMISSION_DENIED:
                errorMsg = "❌ Permissão negada - clique no ícone 🔒 ao lado da URL e permita acesso à localização";
                break;
            case error.POSITION_UNAVAILABLE:
                errorMsg = "❌ Sinal GPS indisponível - tente em área aberta";
                break;
            case error.TIMEOUT:
                errorMsg = "❌ Tempo esgotado - tente novamente";
                break;
        }
        updateGPSStatus(errorMsg, "poor");
        currentLocation = null;
    }

    function stopWatchingLocation() {
        if (watchId) {
            navigator.geolocation.clearWatch(watchId);
            watchId = null;
        }
        if (elements.gpsStatus) {
            elements.gpsStatus.style.display = "none";
        }
    }

    // 🔥 Ativar/desativar GPS conforme checkbox
    if (elements.shareLocation) {
        elements.shareLocation.addEventListener('change', function() {
            if (this.checked) {
                console.log("📍 GPS ativado pelo usuário");
                startWatchingLocation();
            } else {
                console.log("📍 GPS desativado pelo usuário");
                stopWatchingLocation();
                currentLocation = null;
                if (elements.gpsStatus) {
                    elements.gpsStatus.style.display = "none";
                }
            }
        });
    }

    // 🔥 Função para obter localização atual (para o alerta)
    async function getCurrentLocationForAlert() {
        // Se não autorizou, retorna null
        if (!elements.shareLocation || !elements.shareLocation.checked) {
            console.log("⚠️ Localização não autorizada");
            return null;
        }

        // Se já temos localização recente (menos de 30 segundos), usa ela
        if (currentLocation) {
            console.log("📍 Usando localização em cache:", currentLocation);
            return currentLocation;
        }

        // Tenta obter uma posição atual
        if (navigator.geolocation) {
            try {
                console.log("📍 Obtendo localização para o alerta...");
                updateGPSStatus("📍 Obtendo localização...", "info");
                
                const position = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(
                        resolve,
                        reject,
                        {
                            enableHighAccuracy: true,
                            timeout: 10000,
                            maximumAge: 30000
                        }
                    );
                });
                
                const location = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                    accuracy: Math.round(position.coords.accuracy)
                };
                
                console.log("✅ Localização obtida:", location);
                currentLocation = location;
                
                if (location.accuracy < 50) {
                    updateGPSStatus(`✅ GPS ativo: ±${location.accuracy}m`, "good");
                } else {
                    updateGPSStatus(`⚠️ GPS aproximado: ±${location.accuracy}m`, "poor");
                }
                
                return location;
            } catch (error) {
                console.error("❌ Erro ao obter localização:", error);
                handleGPSError(error);
                return null;
            }
        }
        
        return null;
    }

    // Enviar alerta
    async function sendSOSAlert() {
        try {
            if (!selectedSituation) {
                showStatus("⚠️ Selecione a situação", "error");
                return false;
            }

            showStatus("⏳ Preparando alerta...", "info");

            // 🔥 Obtém localização APENAS se autorizado
            let location = null;
            if (elements.shareLocation && elements.shareLocation.checked) {
                location = await getCurrentLocationForAlert();
                if (location) {
                    showStatus("📍 Localização obtida!", "success");
                } else {
                    showStatus("⚠️ Enviando alerta sem localização", "info");
                }
            } else {
                console.log("⚠️ Localização não autorizada - enviando sem GPS");
                showStatus("📤 Enviando alerta (sem localização)", "info");
            }

            const payload = {
                name: elements.name ? elements.name.value.trim() : "Usuária",
                situation: selectedSituation,
                message: elements.message ? elements.message.value.trim() : "",
                location: location,
                timestamp: new Date().toISOString()
            };

            console.log("📤 Enviando payload:", payload);
            showStatus("📤 Enviando alerta...", "info");

            const response = await fetch("/api/send_alert", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();
            console.log("✅ Alerta enviado:", result);

            showStatus("✅ ALERTA ENVIADO!", "success");
            
            if (elements.sos) {
                elements.sos.style.background = "linear-gradient(145deg, #4caf50, #388e3c)";
                setTimeout(() => {
                    elements.sos.style.background = "";
                }, 2000);
            }

            return true;
        } catch (error) {
            console.error("❌ Erro no envio:", error);
            showStatus(`❌ Erro: ${error.message}`, "error");
            return false;
        }
    }

    // Hold
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
        
        if (elements.status && !elements.status.textContent.includes("✅") && !elements.status.textContent.includes("❌")) {
            showStatus("", "info");
        }
    }

    // Events
    if (elements.sos) {
        elements.sos.addEventListener("mousedown", startHold);
        elements.sos.addEventListener("mouseup", cancelHold);
        elements.sos.addEventListener("mouseleave", cancelHold);
        elements.sos.addEventListener("touchstart", startHold, { passive: false });
        elements.sos.addEventListener("touchend", cancelHold);
    }

    // 🔥 INICIAR GPS AUTOMATICAMENTE se checkbox estiver marcado
    if (elements.shareLocation && elements.shareLocation.checked) {
        console.log("📍 Iniciando GPS automaticamente");
        // Pequeno delay para garantir que a página carregou
        setTimeout(() => {
            startWatchingLocation();
        }, 1000);
    }

    console.log("✅ Sistema pronto!");
});