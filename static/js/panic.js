// Sistema SOS Aurora Mulher Segura
// Versão 1.1 - Corrigido e Otimizado
(function() {
    "use strict";
    
    console.log("🌸 Aurora Mulher Segura - Sistema SOS iniciando...");

    // Aguarda DOM estar pronto
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    function init() {
        // ===== ELEMENTOS DOM =====
        const elements = {
            chips: document.querySelectorAll(".chip"),
            sos: document.getElementById("sosBtn"),
            status: document.getElementById("statusMsg") || document.getElementById("status"), // Fallback
            name: document.getElementById("nomeInput") || document.getElementById("name"),
            message: document.getElementById("mensagemInput") || document.getElementById("message")
        };

        // Verifica elementos críticos
        if (!elements.sos) {
            console.error("❌ Erro crítico: Botão SOS não encontrado!");
            return;
        }

        // Se não tiver elemento de status, cria um
        if (!elements.status) {
            console.warn("⚠️ Elemento de status não encontrado, criando...");
            elements.status = document.createElement("div");
            elements.status.id = "statusMsg";
            elements.status.className = "alert center";
            const content = document.querySelector(".content");
            if (content) content.appendChild(elements.status);
        }

        // ===== VARIÁVEIS DE ESTADO =====
        let selectedSituation = "Assédio"; // Valor padrão
        let holdTimer = null;
        let isHolding = false;
        let ultimoAlerta = null;
        let lastLocation = null;

        // Define situação inicial baseada no chip ativo
        document.querySelectorAll(".chip").forEach(chip => {
            if (chip.classList.contains("active")) {
                selectedSituation = chip.dataset.value || "Assédio";
            }
        });

        // ===== FUNÇÕES DE UTILIDADE =====
        function showStatus(message, type = "info") {
            if (!elements.status) return;
            
            elements.status.textContent = message;
            elements.status.className = "alert center";
            
            if (type === "success") {
                elements.status.classList.add("alert-ok");
            } else if (type === "error") {
                elements.status.classList.add("alert-danger");
            }
            
            // Log para debug
            console.log(`📢 Status [${type}]:`, message);
        }

        function clearStatus() {
            if (elements.status) {
                elements.status.textContent = "";
                elements.status.className = "alert center";
            }
        }

        // ===== SISTEMA DE CHIPS =====
        if (elements.chips.length > 0) {
            elements.chips.forEach(chip => {
                chip.addEventListener("click", function(e) {
                    e.preventDefault();
                    
                    // Remove active de todos
                    elements.chips.forEach(c => c.classList.remove("active"));
                    
                    // Ativa o selecionado
                    this.classList.add("active");
                    
                    // Pega o valor
                    selectedSituation = this.dataset.value || this.textContent.trim();
                    
                    console.log("✅ Situação selecionada:", selectedSituation);
                    showStatus(`✓ Situação: ${selectedSituation}`, "success");
                    
                    // Feedback tátil (vibração se disponível)
                    if (navigator.vibrate) navigator.vibrate(50);
                });
            });
        }

        // ===== SISTEMA DE LOCALIZAÇÃO =====
        function getCurrentLocation() {
            return new Promise((resolve, reject) => {
                if (!navigator.geolocation) {
                    reject(new Error("GPS não suportado neste navegador"));
                    return;
                }

                console.log("📍 Solicitando permissão de localização...");
                showStatus("📍 Solicitando localização...", "info");

                // Opções de GPS
                const options = {
                    enableHighAccuracy: true,
                    timeout: 15000,
                    maximumAge: 30000 // Aceita posição com até 30s
                };

                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        console.log("✅ Localização obtida:", position.coords);
                        
                        const location = {
                            lat: position.coords.latitude,
                            lng: position.coords.longitude,
                            accuracy: Math.round(position.coords.accuracy),
                            timestamp: new Date().toISOString()
                        };
                        
                        lastLocation = location;
                        
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
                            case error.PERMISSION_DENIED:
                                errorMessage = "Permissão de GPS negada";
                                break;
                            case error.POSITION_UNAVAILABLE:
                                errorMessage = "Localização indisponível";
                                break;
                            case error.TIMEOUT:
                                errorMessage = "Tempo de GPS esgotado";
                                break;
                        }
                        
                        showStatus(`⚠️ ${errorMessage}`, "info");
                        reject(new Error(errorMessage));
                    },
                    options
                );
            });
        }

        // Inicia monitoramento contínuo de localização
        if (navigator.geolocation) {
            navigator.geolocation.watchPosition(
                (pos) => {
                    lastLocation = {
                        lat: pos.coords.latitude,
                        lng: pos.coords.longitude,
                        accuracy: Math.round(pos.coords.accuracy),
                        timestamp: new Date().toISOString()
                    };
                    
                    // Atualiza display de localização se existir
                    const locTxt = document.getElementById("locTxt");
                    if (locTxt) {
                        locTxt.innerHTML = `Latitude: ${lastLocation.lat}<br>Longitude: ${lastLocation.lng}`;
                    }
                },
                (err) => {
                    console.log("Acompanhamento GPS:", err);
                },
                {
                    enableHighAccuracy: true,
                    maximumAge: 10000,
                    timeout: 5000
                }
            );
        }

        // ===== ENVIO DO ALERTA =====
        async function sendSOSAlert() {
            try {
                console.log("🚨 INICIANDO ENVIO DE ALERTA SOS");
                
                // Validação da situação
                if (!selectedSituation) {
                    showStatus("⚠️ Selecione o tipo de situação", "error");
                    if (navigator.vibrate) navigator.vibrate([100, 100, 100]);
                    return false;
                }

                // Feedback inicial
                showStatus("⏳ Preparando alerta de emergência...", "info");
                if (elements.sos) {
                    elements.sos.style.transform = "scale(0.95)";
                }

                // Obtém nome e mensagem
                const nome = elements.name ? elements.name.value.trim() : "";
                const mensagem = elements.message ? elements.message.value.trim() : "";

                // Monta payload base
                const payload = {
                    name: nome || "Usuária",
                    situation: selectedSituation,
                    message: mensagem || "",
                    timestamp: new Date().toISOString(),
                    userAgent: navigator.userAgent
                };

                console.log("📦 Payload base:", payload);

                // Adiciona localização se disponível
                if (lastLocation) {
                    payload.lat = lastLocation.lat;
                    payload.lng = lastLocation.lng;
                    payload.accuracy = lastLocation.accuracy;
                    console.log("📍 Localização adicionada:", lastLocation);
                } else {
                    // Tenta obter localização agora
                    try {
                        showStatus("📍 Obtendo localização...", "info");
                        const location = await getCurrentLocation();
                        payload.lat = location.lat;
                        payload.lng = location.lng;
                        payload.accuracy = location.accuracy;
                    } catch (locationError) {
                        console.warn("⚠️ Falha no GPS:", locationError.message);
                        showStatus("⚠️ Enviando alerta sem localização", "info");
                    }
                }

                // Feedback de envio
                showStatus("📤 Enviando alerta para contatos de confiança...", "info");
                if (navigator.vibrate) navigator.vibrate(200);

                // Verifica conectividade
                if (!navigator.onLine) {
                    // Salva para envio posterior
                    try {
                        const pendentes = JSON.parse(localStorage.getItem('alertas_pendentes') || '[]');
                        pendentes.push(payload);
                        localStorage.setItem('alertas_pendentes', JSON.stringify(pendentes));
                        showStatus("📴 Offline - alerta salvo para envio automático", "info");
                        
                        // Redireciona para página offline
                        if (confirm("Você está offline. O alerta será enviado quando a internet voltar. Deseja ver o modo offline?")) {
                            window.location.href = "/offline";
                        }
                        
                        return true;
                    } catch (e) {
                        console.error("Erro ao salvar offline:", e);
                    }
                }

                // Envia para API
                console.log("🌐 Enviando requisição para /api/send_alert");
                
                // Timeout de 10 segundos para o fetch
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 10000);

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

                console.log("📥 Resposta recebida:", response.status);

                // Processa resposta
                if (!response.ok) {
                    const errorText = await response.text().catch(() => "Erro desconhecido");
                    throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 100)}`);
                }

                const result = await response.json();
                console.log("📄 Resposta JSON:", result);

                // Sucesso!
                if (result && result.ok) {
                    showStatus("✅ ALERTA ENVIADO! Contatos notificados.", "success");
                    
                    // Salva o último alerta
                    ultimoAlerta = payload;
                    
                    // Feedback visual de sucesso
                    if (elements.sos) {
                        elements.sos.style.background = "linear-gradient(145deg, #4caf50, #388e3c)";
                        setTimeout(() => {
                            if (elements.sos) {
                                elements.sos.style.background = "";
                                elements.sos.style.transform = "";
                            }
                        }, 1500);
                    }
                    
                    // Vibração de sucesso
                    if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
                    
                    return true;
                } else {
                    throw new Error(result?.message || "Erro desconhecido no servidor");
                }

            } catch (error) {
                console.error("❌ Erro crítico no envio:", error);
                
                let errorMsg = error.message || "Falha na comunicação";
                if (error.name === "AbortError") {
                    errorMsg = "Tempo limite excedido";
                }
                
                showStatus(`❌ Erro: ${errorMsg}`, "error");
                
                // Feedback visual de erro
                if (elements.sos) {
                    elements.sos.style.background = "linear-gradient(145deg, #9c27b0, #7b1fa2)";
                    setTimeout(() => {
                        if (elements.sos) {
                            elements.sos.style.background = "";
                            elements.sos.style.transform = "";
                        }
                    }, 1000);
                }
                
                // Vibração de erro
                if (navigator.vibrate) navigator.vibrate(500);
                
                return false;
            }
        }

        // ===== SISTEMA DE HOLD =====
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
            
            // Só limpa o status se não tiver mensagem de sucesso
            if (elements.status && !elements.status.textContent.includes("✅")) {
                clearStatus();
            }
            
            isHolding = false;
        }

        // ===== EVENT LISTENERS DO BOTÃO SOS =====
        if (elements.sos) {
            // Mouse events (desktop)
            elements.sos.addEventListener("mousedown", startHold);
            elements.sos.addEventListener("mouseup", cancelHold);
            elements.sos.addEventListener("mouseleave", cancelHold);
            
            // Touch events (mobile)
            elements.sos.addEventListener("touchstart", startHold, { passive: false });
            elements.sos.addEventListener("touchend", cancelHold);
            elements.sos.addEventListener("touchcancel", cancelHold);
            
            // Previne menu de contexto
            elements.sos.addEventListener("contextmenu", (e) => e.preventDefault());
            
            // Acessibilidade por teclado
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
            
            console.log("✅ Eventos do botão SOS configurados");
        }

        // ===== SISTEMA DE PARADA SUSPEITA =====
        let ultimoMovimento = Date.now();

        if (navigator.geolocation) {
            navigator.geolocation.watchPosition(
                () => {
                    ultimoMovimento = Date.now();
                },
                () => {},
                { enableHighAccuracy: true }
            );

            setInterval(() => {
                let parado = (Date.now() - ultimoMovimento) / 1000;
                if (parado > 120) { // 2 minutos parado
                    console.log("⚠️ Parada suspeita detectada");
                    // Opcional: mostrar aviso
                    if (elements.status && !elements.status.textContent.includes("ALERTA")) {
                        showStatus("⚠️ Você está parada há muito tempo. Precisa de ajuda?", "info");
                    }
                }
            }, 30000);
        }

        // ===== VERIFICAÇÃO DE ALERTAS PENDENTES =====
        function verificarAlertasPendentes() {
            try {
                const pendentes = JSON.parse(localStorage.getItem('alertas_pendentes') || '[]');
                if (pendentes.length > 0 && navigator.onLine) {
                    showStatus(`⏳ ${pendentes.length} alerta(s) pendente(s) aguardando envio...`, "info");
                    
                    // Tenta enviar o primeiro pendente
                    // (Implementar se necessário)
                } else if (pendentes.length > 0) {
                    showStatus(`📴 ${pendentes.length} alerta(s) salvo(s) offline`, "info");
                }
            } catch (e) {
                console.error("Erro ao verificar pendentes:", e);
            }
        }

        // ===== DIAGNÓSTICO INICIAL =====
        console.log("✅ Sistema Aurora inicializado com sucesso!");
        console.log("📊 Diagnóstico:", {
            chips: elements.chips.length,
            gps: !!navigator.geolocation,
            vibrate: !!navigator.vibrate,
            online: navigator.onLine,
            userAgent: navigator.userAgent
        });

        // Verifica conectividade
        if (!navigator.onLine) {
            showStatus("⚠️ Modo offline - verifique sua internet", "info");
            verificarAlertasPendentes();
        } else {
            showStatus("✅ Sistema pronto - selecione uma situação", "success");
        }

        // Monitora mudanças de conectividade
        window.addEventListener('online', () => {
            showStatus("✅ Conexão restabelecida", "success");
            verificarAlertasPendentes();
        });
        
        window.addEventListener('offline', () => {
            showStatus("⚠️ Modo offline ativado", "info");
        });
    }
})();