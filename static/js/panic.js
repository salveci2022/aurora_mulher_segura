// Sistema SOS Aurora Mulher Segura
// Versão 3.0 - GPS EXATO + SIRENE AUTOMÁTICA
(function() {
    "use strict";
    console.log("🌸 Aurora Mulher Segura - Sistema SOS v3.0 iniciando...");

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    function init() {
        const elements = {
            chips: document.querySelectorAll(".chip"),
            sos: document.getElementById("sosBtn"),
            status: document.getElementById("statusMsg") || document.getElementById("status"),
            name: document.getElementById("nomeInput") || document.getElementById("name"),
            message: document.getElementById("mensagemInput") || document.getElementById("message"),
            gpsStatus: document.getElementById("gpsStatus")
        };

        if (!elements.sos) {
            console.error("❌ Erro crítico: Botão SOS não encontrado!");
            return;
        }

        if (!elements.status) {
            elements.status = document.createElement("div");
            elements.status.id = "statusMsg";
            elements.status.className = "alert center";
            const content = document.querySelector(".content");
            if (content) content.appendChild(elements.status);
        }

        let selectedSituation = "Assédio";
        let holdTimer = null;
        let isHolding = false;
        let lastLocation = null;
        let gpsAccuracy = 999;
        let gpsReadings = 0;

        // ===== GPS DE ALTA PRECISÃO =====
        function initHighAccuracyGPS() {
            if (!navigator.geolocation) {
                updateGPSStatus('error', 'GPS não suportado');
                return;
            }

            // Opções de MÁXIMA precisão
            const highAccuracyOptions = {
                enableHighAccuracy: true,      // ✅ Força GPS de alta precisão
                timeout: 30000,                 // 30 segundos timeout
                maximumAge: 0,                  // ✅ Não usar cache, sempre novo
                frequency: 1000                 // Atualiza a cada 1 segundo
            };

            // Primeira leitura imediata
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    gpsReadings++;
                    const acc = Math.round(position.coords.accuracy);
                    
                    lastLocation = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                        accuracy: acc,
                        timestamp: new Date().toISOString(),
                        altitude: position.coords.altitude,
                        heading: position.coords.heading,
                        speed: position.coords.speed
                    };

                    // Determina qualidade do GPS
                    if (acc <= 10) {
                        updateGPSStatus('excellent', `±${acc}m (EXCELENTE)`);
                        gpsAccuracy = acc;
                    } else if (acc <= 25) {
                        updateGPSStatus('good', `±${acc}m (BOM)`);
                        gpsAccuracy = acc;
                    } else if (acc <= 50) {
                        updateGPSStatus('warning', `±${acc}m (MÉDIO)`);
                        gpsAccuracy = acc;
                    } else {
                        updateGPSStatus('error', `±${acc}m (RUIM)`);
                        gpsAccuracy = acc;
                    }

                    console.log(`✅ GPS ${gpsReadings}ª leitura:`, lastLocation);
                },
                (error) => {
                    let msg = 'Erro GPS';
                    switch(error.code) {
                        case error.PERMISSION_DENIED: msg = 'Permissão negada'; break;
                        case error.POSITION_UNAVAILABLE: msg = 'Indisponível'; break;
                        case error.TIMEOUT: msg = 'Timeout'; break;
                    }
                    updateGPSStatus('error', msg);
                },
                highAccuracyOptions
            );

            // Monitoramento contínuo para manter precisão
            navigator.geolocation.watchPosition(
                (position) => {
                    gpsReadings++;
                    const acc = Math.round(position.coords.accuracy);
                    
                    // Só atualiza se for mais preciso
                    if (acc < gpsAccuracy || gpsAccuracy === 999) {
                        lastLocation = {
                            lat: position.coords.latitude,
                            lng: position.coords.longitude,
                            accuracy: acc,
                            timestamp: new Date().toISOString(),
                            altitude: position.coords.altitude,
                            heading: position.coords.heading,
                            speed: position.coords.speed
                        };
                        gpsAccuracy = acc;

                        if (acc <= 10) {
                            updateGPSStatus('excellent', `±${acc}m (EXCELENTE)`);
                        } else if (acc <= 25) {
                            updateGPSStatus('good', `±${acc}m (BOM)`);
                        }
                    }

                    console.log(`📍 GPS contínuo ${gpsReadings}ª: ±${acc}m`);
                },
                (err) => console.log('Watch error:', err),
                highAccuracyOptions
            );

            // Força nova leitura a cada 5 segundos para manter precisão
            setInterval(() => {
                if (navigator.geolocation && gpsReadings < 5) {
                    navigator.geolocation.getCurrentPosition(
                        (pos) => {
                            const acc = Math.round(pos.coords.accuracy);
                            if (acc < gpsAccuracy) {
                                lastLocation.lat = pos.coords.latitude;
                                lastLocation.lng = pos.coords.longitude;
                                lastLocation.accuracy = acc;
                                gpsAccuracy = acc;
                                console.log('🎯 GPS refinado:', acc, 'metros');
                            }
                        },
                        null,
                        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
                    );
                }
            }, 5000);
        }

        function updateGPSStatus(quality, text) {
            if (elements.gpsStatus) {
                const colors = {
                    'excellent': '#4caf50',
                    'good': '#8bc34a',
                    'warning': '#ff9800',
                    'error': '#f44336'
                };
                const icons = {
                    'excellent': '🟢',
                    'good': '🟡',
                    'warning': '🟠',
                    'error': '🔴'
                };
                elements.gpsStatus.innerHTML = `${icons[quality] || '🔴'} ${text}`;
                elements.gpsStatus.style.color = colors[quality] || '#f44336';
            }
        }

        // Inicializa GPS imediatamente
        initHighAccuracyGPS();

        // ===== CHIPS =====
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
            console.log(`📢 Status [${type}]:`, message);
        }

        // ===== ENVIO DO ALERTA COM GPS EXATO =====
        async function sendSOSAlert() {
            try {
                console.log("🚨 INICIANDO ENVIO DE ALERTA SOS");

                if (!selectedSituation) {
                    showStatus("⚠️ Selecione o tipo de situação", "error");
                    if (navigator.vibrate) navigator.vibrate([100, 100, 100]);
                    return false;
                }

                showStatus("⏳ Preparando alerta de emergência...", "info");
                if (elements.sos) elements.sos.style.transform = "scale(0.95)";

                const nome = elements.name ? elements.name.value.trim() : "";
                const mensagem = elements.message ? elements.message.value.trim() : "";

                const payload = {
                    name: nome || "Usuária",
                    situation: selectedSituation,
                    message: mensagem || "",
                    timestamp: new Date().toISOString(),
                    userAgent: navigator.userAgent
                };

                // Aguarda GPS mais preciso se necessário
                if (gpsAccuracy > 50 && gpsReadings < 3) {
                    showStatus("📍 Aguardando GPS mais preciso...", "info");
                    await new Promise(resolve => setTimeout(resolve, 3000));
                }

                if (lastLocation) {
                    payload.lat = lastLocation.lat;
                    payload.lng = lastLocation.lng;
                    payload.accuracy = lastLocation.accuracy;
                    payload.altitude = lastLocation.altitude;
                    payload.heading = lastLocation.heading;
                    payload.speed = lastLocation.speed;
                    payload.gps_readings = gpsReadings;
                    console.log("📍 Localização EXATA enviada:", lastLocation);
                } else {
                    try {
                        showStatus("📍 Obtendo localização...", "info");
                        const location = await getCurrentLocation();
                        payload.lat = location.lat;
                        payload.lng = location.lng;
                        payload.accuracy = location.accuracy;
                    } catch (locationError) {
                        console.warn("⚠️ Falha no GPS:", locationError.message);
                    }
                }

                showStatus("📤 Enviando alerta...", "info");
                if (navigator.vibrate) navigator.vibrate(200);

                if (!navigator.onLine) {
                    const pendentes = JSON.parse(localStorage.getItem('alertas_pendentes') || '[]');
                    pendentes.push(payload);
                    localStorage.setItem('alertas_pendentes', JSON.stringify(pendentes));
                    showStatus("📴 Offline - alerta salvo", "info");
                    if (confirm("Offline. Enviar quando online?")) {
                        window.location.href = "/offline";
                    }
                    return true;
                }

                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 15000);

                const response = await fetch("/api/send_alert", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    body: JSON.stringify(payload),
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                if (!response.ok) {
                    const errorText = await response.text().catch(() => "Erro desconhecido");
                    throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 100)}`);
                }

                const result = await response.json();

                if (result && result.ok) {
                    showStatus("✅ ALERTA ENVIADO! Contatos notificados.", "success");
                    if (elements.sos) {
                        elements.sos.style.background = "linear-gradient(145deg, #4caf50, #388e3c)";
                        setTimeout(() => {
                            if (elements.sos) {
                                elements.sos.style.background = "";
                                elements.sos.style.transform = "";
                            }
                        }, 1500);
                    }
                    if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
                    return true;
                } else {
                    throw new Error(result?.message || "Erro desconhecido");
                }

            } catch (error) {
                console.error("❌ Erro crítico:", error);
                let errorMsg = error.message || "Falha na comunicação";
                if (error.name === "AbortError") errorMsg = "Tempo limite excedido";
                showStatus(`❌ Erro: ${errorMsg}`, "error");
                if (elements.sos) {
                    elements.sos.style.background = "linear-gradient(145deg, #9c27b0, #7b1fa2)";
                    setTimeout(() => {
                        if (elements.sos) {
                            elements.sos.style.background = "";
                            elements.sos.style.transform = "";
                        }
                    }, 1000);
                }
                if (navigator.vibrate) navigator.vibrate(500);
                return false;
            }
        }

        function getCurrentLocation() {
            return new Promise((resolve, reject) => {
                if (!navigator.geolocation) {
                    reject(new Error("GPS não suportado"));
                    return;
                }

                const options = {
                    enableHighAccuracy: true,
                    timeout: 30000,
                    maximumAge: 0
                };

                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const location = {
                            lat: position.coords.latitude,
                            lng: position.coords.longitude,
                            accuracy: Math.round(position.coords.accuracy),
                            timestamp: new Date().toISOString()
                        };
                        lastLocation = location;
                        resolve(location);
                    },
                    (error) => {
                        reject(new Error("Erro GPS"));
                    },
                    options
                );
            });
        }

        // ===== HOLD =====
        function startHold(e) {
            e.preventDefault();
            if (isHolding) return;
            isHolding = true;
            if (elements.sos) elements.sos.classList.add("holding");
            showStatus("⚠️ Segure por 1 segundo...", "info");
            if (navigator.vibrate) navigator.vibrate(50);
            holdTimer = setTimeout(() => {
                if (isHolding) {
                    console.log("⏰ Hold completado - enviando");
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
            if (elements.sos) elements.sos.classList.remove("holding");
            if (elements.status && !elements.status.textContent.includes("✅")) {
                elements.status.textContent = "";
                elements.status.className = "alert center";
            }
            isHolding = false;
        }

        // ===== EVENT LISTENERS =====
        if (elements.sos) {
            elements.sos.addEventListener("mousedown", startHold);
            elements.sos.addEventListener("mouseup", cancelHold);
            elements.sos.addEventListener("mouseleave", cancelHold);
            elements.sos.addEventListener("touchstart", startHold, { passive: false });
            elements.sos.addEventListener("touchend", cancelHold);
            elements.sos.addEventListener("touchcancel", cancelHold);
            elements.sos.addEventListener("contextmenu", (e) => e.preventDefault());
            elements.sos.setAttribute("tabindex", "0");
            elements.sos.setAttribute("role", "button");
            elements.sos.setAttribute("aria-label", "Botão de pânico - segure para enviar alerta");
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
        }

        console.log("✅ Sistema Aurora v3.0 inicializado!");
        console.log("📊 GPS:", {
            supported: !!navigator.geolocation,
            highAccuracy: true,
            readings: gpsReadings,
            accuracy: gpsAccuracy
        });
    }
})();