// ============================================
// AURORA v4.0 - SISTEMA DE LOCALIZAÇÃO AVANÇADO
// ============================================
document.addEventListener("DOMContentLoaded", function() {
    console.log("🌸 Aurora - Sistema SOS avançado iniciando...");
    
    const elements = {
        chips: document.querySelectorAll(".chip"),
        sos: document.getElementById("sosBtn"),
        status: document.getElementById("status"),
        name: document.getElementById("name"),
        message: document.getElementById("message"),
        shareLocation: document.getElementById("shareLocation"),
        gpsStatus: document.getElementById("gpsStatus"),
        gpsText: document.getElementById("gpsText"),
        permissionHelp: document.getElementById("permissionHelp")
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
    let locationSource = "none"; // gps, ip, none
    
    // ============================================
    // SISTEMA DE PERMISSÃO INTELIGENTE
    // ============================================
    
    async function checkPermissionState() {
        if (!navigator.permissions || !navigator.permissions.query) {
            console.log("⚠️ API de permissão não suportada");
            return "unknown";
        }

        try {
            const permission = await navigator.permissions.query({ name: 'geolocation' });
            console.log("📌 Status da permissão:", permission.state);
            
            // Monitora mudanças na permissão
            permission.onchange = function() {
                console.log("🔄 Permissão mudou para:", this.state);
                if (this.state === 'granted') {
                    updateGPSStatus("✅ Permissão concedida! Iniciando GPS...", "good");
                    startWatchingLocation();
                    if (elements.permissionHelp) {
                        elements.permissionHelp.style.display = "none";
                    }
                } else if (this.state === 'denied') {
                    updateGPSStatus("❌ Permissão negada - ative nas configurações", "poor");
                    if (elements.permissionHelp) {
                        elements.permissionHelp.style.display = "block";
                    }
                }
            };
            
            return permission.state;
        } catch (error) {
            console.log("Erro ao verificar permissão:", error);
            return "unknown";
        }
    }
    
    // ============================================
    // FALLBACK: GEOLOCALIZAÇÃO POR IP
    // ============================================
    
    async function getLocationByIP() {
        console.log("🌐 Tentando localização por IP...");
        updateGPSStatus("🌐 Obtendo localização aproximada por IP...", "info");
        
        try {
            // Usa ipapi.co (gratuito, sem autenticação)
            const response = await fetch('https://ipapi.co/json/');
            const data = await response.json();
            
            if (data && data.latitude && data.longitude) {
                console.log("✅ Localização por IP obtida:", data);
                return {
                    lat: data.latitude,
                    lng: data.longitude,
                    accuracy: 5000, // IP tem precisão de ~5km
                    source: 'ip',
                    city: data.city,
                    region: data.region
                };
            }
        } catch (error) {
            console.error("❌ Erro na localização por IP:", error);
        }
        
        // Fallback 2: ipinfo.io
        try {
            const response = await fetch('https://ipinfo.io/json?token='); // Token opcional
            const data = await response.json();
            
            if (data && data.loc) {
                const [lat, lng] = data.loc.split(',');
                console.log("✅ Localização por ipinfo.io:", data);
                return {
                    lat: parseFloat(lat),
                    lng: parseFloat(lng),
                    accuracy: 5000,
                    source: 'ip',
                    city: data.city,
                    region: data.region
                };
            }
        } catch (error) {
            console.error("❌ Erro no ipinfo.io:", error);
        }
        
        return null;
    }
    
    // ============================================
    // SISTEMA GPS PRINCIPAL
    // ============================================
    
    function updateGPSStatus(message, type = "info", showHelp = false) {
        if (!elements.gpsStatus || !elements.gpsText) return;
        
        elements.gpsStatus.style.display = "block";
        elements.gpsText.innerHTML = message;
        
        elements.gpsStatus.classList.remove("good", "poor", "active");
        
        if (type === "good") {
            elements.gpsStatus.classList.add("good", "active");
        } else if (type === "poor") {
            elements.gpsStatus.classList.add("poor", "active");
        } else if (type === "info") {
            elements.gpsStatus.classList.add("active");
        }
        
        if (elements.permissionHelp) {
            elements.permissionHelp.style.display = showHelp ? "block" : "none";
        }
    }

    function showPermissionInstructions() {
        const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
        
        let instructions = "";
        if (isMobile) {
            instructions = "📱 No celular: vá em Configurações > Apps > Navegador > Permissões > Localização > Permitir";
        } else {
            instructions = "💻 No computador: clique no ícone 🔒 ao lado da URL e permita 'Localização'";
        }
        
        if (elements.permissionHelp) {
            elements.permissionHelp.innerHTML = `🔒 <strong>Permissão negada?</strong> ${instructions}`;
            elements.permissionHelp.style.display = "block";
        }
        
        updateGPSStatus(`❌ Permissão negada - ${isMobile ? 'ative nas configurações' : 'clique no cadeado'}`, "poor");
    }

    async function startWatchingLocation() {
        if (!navigator.geolocation) {
            updateGPSStatus("❌ GPS não suportado neste dispositivo", "poor");
            
            // Fallback para IP
            const ipLocation = await getLocationByIP();
            if (ipLocation) {
                currentLocation = ipLocation;
                locationSource = 'ip';
                updateGPSStatus(`🌐 Localização aproximada: ${ipLocation.city || ''} (por IP)`, "info");
            }
            return;
        }

        // Verifica estado da permissão
        const permissionState = await checkPermissionState();
        
        if (permissionState === 'denied') {
            showPermissionInstructions();
            
            // Tenta fallback por IP mesmo com permissão negada
            const ipLocation = await getLocationByIP();
            if (ipLocation) {
                currentLocation = ipLocation;
                locationSource = 'ip';
                updateGPSStatus(`🌐 Localização aproximada por IP (precisão ~5km)`, "info");
            }
            return;
        }

        updateGPSStatus("📍 Solicitando permissão de localização...", "info");

        // Tenta GPS primeiro
        navigator.geolocation.getCurrentPosition(
            // Sucesso
            (position) => {
                console.log("✅ GPS concedido!");
                locationSource = 'gps';
                
                // Inicia watch de alta precisão
                watchId = navigator.geolocation.watchPosition(
                    (pos) => {
                        currentLocation = {
                            lat: pos.coords.latitude,
                            lng: pos.coords.longitude,
                            accuracy: Math.round(pos.coords.accuracy),
                            source: 'gps'
                        };
                        
                        console.log("📍 GPS atualizado:", currentLocation);
                        
                        if (currentLocation.accuracy < 50) {
                            updateGPSStatus(`✅ GPS preciso: ±${currentLocation.accuracy}m`, "good");
                        } else {
                            updateGPSStatus(`⚠️ GPS aproximado: ±${currentLocation.accuracy}m`, "poor");
                        }
                        
                        if (elements.permissionHelp) {
                            elements.permissionHelp.style.display = "none";
                        }
                    },
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
            // Erro
            async (error) => {
                console.error("❌ Erro GPS:", error);
                
                if (error.code === error.PERMISSION_DENIED) {
                    showPermissionInstructions();
                } else {
                    handleGPSError(error);
                }
                
                // Fallback para IP
                const ipLocation = await getLocationByIP();
                if (ipLocation) {
                    currentLocation = ipLocation;
                    locationSource = 'ip';
                    updateGPSStatus(`🌐 Localização aproximada por IP`, "info");
                }
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
                errorMsg = "❌ Permissão negada";
                break;
            case error.POSITION_UNAVAILABLE:
                errorMsg = "❌ Sinal indisponível - tente em área aberta";
                break;
            case error.TIMEOUT:
                errorMsg = "❌ Tempo esgotado - tente novamente";
                break;
        }
        updateGPSStatus(errorMsg, "poor");
    }

    function stopWatchingLocation() {
        if (watchId) {
            navigator.geolocation.clearWatch(watchId);
            watchId = null;
        }
    }

    // ============================================
    // OBTENÇÃO DE LOCALIZAÇÃO PARA ALERTA
    // ============================================
    
    async function getLocationForAlert() {
        // Se não autorizou, retorna null
        if (!elements.shareLocation || !elements.shareLocation.checked) {
            console.log("⚠️ Localização não autorizada pelo checkbox");
            return null;
        }

        // Se já temos localização (GPS ou IP), usa ela
        if (currentLocation) {
            console.log(`📍 Usando localização em cache (fonte: ${currentLocation.source || 'gps'}):`, currentLocation);
            return currentLocation;
        }

        // Tenta GPS
        if (navigator.geolocation) {
            try {
                console.log("📍 Tentando GPS para o alerta...");
                updateGPSStatus("📍 Obtendo localização...", "info");
                
                const position = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(
                        resolve,
                        reject,
                        {
                            enableHighAccuracy: true,
                            timeout: 8000,
                            maximumAge: 30000
                        }
                    );
                });
                
                const location = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                    accuracy: Math.round(position.coords.accuracy),
                    source: 'gps'
                };
                
                console.log("✅ GPS obtido:", location);
                currentLocation = location;
                locationSource = 'gps';
                return location;
                
            } catch (gpsError) {
                console.log("⚠️ GPS falhou, tentando IP...", gpsError);
            }
        }
        
        // Fallback para IP
        console.log("🌐 Tentando localização por IP...");
        const ipLocation = await getLocationByIP();
        if (ipLocation) {
            currentLocation = ipLocation;
            locationSource = 'ip';
            updateGPSStatus(`🌐 Usando localização por IP`, "info");
            return ipLocation;
        }
        
        return null;
    }

    // ============================================
    // ENVIO DO ALERTA
    // ============================================
    
    async function sendSOSAlert() {
        try {
            if (!selectedSituation) {
                showStatus("⚠️ Selecione a situação", "error");
                return false;
            }

            showStatus("⏳ Preparando alerta...", "info");

            // Obtém localização
            let location = null;
            let locationInfo = "";
            
            if (elements.shareLocation && elements.shareLocation.checked) {
                location = await getLocationForAlert();
                
                if (location) {
                    if (location.source === 'gps') {
                        locationInfo = `📍 GPS: ±${location.accuracy}m`;
                        showStatus(`📍 ${locationInfo}`, "success");
                    } else if (location.source === 'ip') {
                        locationInfo = `🌐 IP: ${location.city || ''} (aproximado)`;
                        showStatus(`🌐 ${locationInfo}`, "info");
                    }
                } else {
                    showStatus("⚠️ Enviando sem localização", "info");
                }
            } else {
                showStatus("📤 Enviando alerta (sem localização)", "info");
            }

            const payload = {
                name: elements.name ? elements.name.value.trim() : "Usuária",
                situation: selectedSituation,
                message: elements.message ? elements.message.value.trim() : "",
                location: location,
                locationSource: location?.source || 'none',
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent
            };

            console.log("📤 Enviando payload:", payload);
            showStatus("📤 Enviando alerta...", "info");

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000);

            const response = await fetch("/api/send_alert", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();
            console.log("✅ Alerta enviado:", result);

            // Mensagem personalizada com fonte da localização
            let successMsg = "✅ ALERTA ENVIADO!";
            if (location) {
                successMsg += ` ${location.source === 'gps' ? '📍' : '🌐'}`;
            }
            showStatus(successMsg, "success");
            
            if (elements.sos) {
                elements.sos.style.background = "linear-gradient(145deg, #4caf50, #388e3c)";
                setTimeout(() => {
                    elements.sos.style.background = "";
                }, 2000);
            }

            return true;
        } catch (error) {
            console.error("❌ Erro no envio:", error);
            
            if (error.name === 'AbortError') {
                showStatus("❌ Tempo limite excedido", "error");
            } else {
                showStatus(`❌ Erro: ${error.message}`, "error");
            }
            return false;
        }
    }

    // ============================================
    // SISTEMA DE HOLD (SEGURAR BOTÃO)
    // ============================================
    
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
    }

    // ============================================
    // EVENT LISTENERS
    // ============================================
    
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

    // Botão SOS
    if (elements.sos) {
        elements.sos.addEventListener("mousedown", startHold);
        elements.sos.addEventListener("mouseup", cancelHold);
        elements.sos.addEventListener("mouseleave", cancelHold);
        elements.sos.addEventListener("touchstart", startHold, { passive: false });
        elements.sos.addEventListener("touchend", cancelHold);
    }

    // Checkbox de localização
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
                if (elements.permissionHelp) {
                    elements.permissionHelp.style.display = "none";
                }
            }
        });
    }

    // ============================================
    // INICIALIZAÇÃO
    // ============================================
    
    // Verifica permissão ao carregar
    checkPermissionState();
    
    // Se checkbox marcado, inicia GPS
    if (elements.shareLocation && elements.shareLocation.checked) {
        console.log("📍 Iniciando GPS automaticamente");
        setTimeout(() => {
            startWatchingLocation();
        }, 1000);
    }

    // Detecta quando a página ganha foco (útil para quando volta das configurações)
    window.addEventListener('focus', function() {
        console.log("🔄 Página focada, verificando permissão...");
        if (elements.shareLocation && elements.shareLocation.checked) {
            startWatchingLocation();
        }
    });

    console.log("✅ Sistema avançado pronto!");
});