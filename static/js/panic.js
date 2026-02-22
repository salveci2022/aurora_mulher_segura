// Sistema SOS Aurora Mulher Segura
// Versão 1.0 - Completo e Testado

document.addEventListener("DOMContentLoaded", function() {
    console.log("🌸 Aurora Mulher Segura - Sistema SOS iniciando...");

    // ===== ELEMENTOS DOM =====
    const elements = {
        chips: document.querySelectorAll(".chip"),
        sos: document.getElementById("sosBtn"),
        status: document.getElementById("status"),
        share: document.getElementById("shareLocation"),
        name: document.getElementById("name"),
        message: document.getElementById("message"),
        btnReset: document.getElementById("btnReset"),
        btnClear: document.getElementById("btnClear"),
        btnExit: document.getElementById("btnExit")
    };

    // Verifica elementos críticos
    if (!elements.sos || !elements.status) {
        console.error("❌ Erro crítico: Elementos necessários não encontrados!");
        showStatus("❌ Erro no sistema", "error");
        return;
    }

    // ===== VARIÁVEIS DE ESTADO =====
    let selectedSituation = "";
    let holdTimer = null;
    let isHolding = false;

    // ===== FUNÇÕES DE UTILIDADE =====
    function showStatus(message, type = "info") {
        if (!elements.status) return;
        
        elements.status.textContent = message;
        elements.status.style.color = 
            type === "success" ? "#4caf50" :
            type === "error" ? "#f44336" :
            type === "warning" ? "#ff9800" : "#2196f3";
        elements.status.style.fontWeight = "500";
        
        console.log(`📌 Status [${type}]: ${message}`);
    }

    function clearStatus() {
        if (elements.status) {
            elements.status.textContent = "";
            elements.status.style.color = "";
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
                
                // Pega o texto (removendo emojis se houver)
                let text = this.textContent.trim();
                // Remove emojis comuns do início
                text = text.replace(/^[🔴🗣️👀⚠️]+\s*/, "");
                selectedSituation = text;
                
                console.log("✅ Situação selecionada:", selectedSituation);
                showStatus(`✓ Situação: ${selectedSituation}`, "success");
                
                // Feedback tátil (vibração se disponível)
                if (navigator.vibrate) navigator.vibrate(50);
            });
        });
    }

    // ===== SISTEMA DE LOCALIZAÇÃO =====
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
                    
                    // Feedback de precisão
                    if (location.accuracy < 50) {
                        showStatus(`📍 Localização precisa (${location.accuracy}m)`, "success");
                    } else {
                        showStatus(`📍 Localização aproximada (${location.accuracy}m)`, "warning");
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
                    
                    showStatus(`⚠️ ${errorMessage}`, "warning");
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

    // ===== ENVIO DO ALERTA =====
    async function sendSOSAlert() {
        try {
            console.log("🚨 INICIANDO ENVIO DE ALERTA SOS");
            
            // Validação da situação
            if (!selectedSituation) {
                showStatus("⚠️ Selecione o tipo de situação", "warning");
                if (navigator.vibrate) navigator.vibrate([100, 100, 100]);
                return false;
            }

            // Feedback inicial
            showStatus("⏳ Preparando alerta de emergência...", "info");
            if (elements.sos) {
                elements.sos.style.transform = "scale(0.95)";
            }

            // Monta payload base
            const payload = {
                name: elements.name ? elements.name.value.trim() : "Anônimo",
                situation: selectedSituation,
                message: elements.message ? elements.message.value.trim() : "",
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                language: navigator.language
            };

            console.log("📦 Payload base:", payload);

            // Adiciona localização se marcado
            if (elements.share && elements.share.checked) {
                try {
                    showStatus("📍 Obtendo localização exata...", "info");
                    const location = await getCurrentLocation();
                    payload.location = location;
                    console.log("📍 Localização adicionada:", location);
                } catch (locationError) {
                    console.warn("⚠️ Falha no GPS:", locationError);
                    showStatus("⚠️ Enviando alerta sem localização", "warning");
                }
            } else {
                console.log("📍 Localização não solicitada");
            }

            // Feedback de envio
            showStatus("📤 Enviando alerta para contatos de confiança...", "info");
            if (navigator.vibrate) navigator.vibrate(200);

            // Envia para API
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

            // Processa resposta
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
            }

            const result = await response.json();
            console.log("📄 Resposta JSON:", result);

            // Sucesso!
            if (result.ok) {
                showStatus("✅ ALERTA ENVIADO! Contatos notificados.", "success");
                
                // Feedback visual de sucesso
                if (elements.sos) {
                    elements.sos.style.background = "linear-gradient(145deg, #4caf50, #388e3c)";
                    setTimeout(() => {
                        elements.sos.style.background = "linear-gradient(145deg, #d32f2f, #b71c1c)";
                        elements.sos.style.transform = "";
                    }, 1500);
                }
                
                // Vibração de sucesso
                if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
                
                return true;
            } else {
                throw new Error(result.message || "Erro desconhecido no servidor");
            }

        } catch (error) {
            console.error("❌ Erro crítico no envio:", error);
            
            showStatus(`❌ Erro: ${error.message || "Falha na comunicação"}`, "error");
            
            // Feedback visual de erro
            if (elements.sos) {
                elements.sos.style.background = "linear-gradient(145deg, #9c27b0, #7b1fa2)";
                setTimeout(() => {
                    elements.sos.style.background = "linear-gradient(145deg, #d32f2f, #b71c1c)";
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
        
        // Feedback visual
        if (elements.sos) {
            elements.sos.classList.add("holding");
        }
        
        showStatus("⚠️ Segure por 1 segundo para enviar SOS", "warning");
        if (navigator.vibrate) navigator.vibrate(50);

        // Timer para enviar
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
        
        // Limpa timer
        if (holdTimer) {
            clearTimeout(holdTimer);
            holdTimer = null;
        }
        
        // Remove feedback visual
        if (elements.sos) {
            elements.sos.classList.remove("holding");
        }
        
        // Limpa status se não houver mensagem
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

    // ===== BOTÕES DE AÇÃO =====
    if (elements.btnReset) {
        elements.btnReset.addEventListener("click", () => {
            console.log("🔄 Resetando formulário");
            
            // Limpa inputs
            if (elements.name) elements.name.value = "Maria Silva";
            if (elements.message) elements.message.value = "Preciso de ajuda, estou em situação de risco!";
            
            // Limpa chips
            elements.chips.forEach(c => c.classList.remove("active"));
            selectedSituation = "";
            
            // Marca checkbox
            if (elements.share) elements.share.checked = true;
            
            clearStatus();
            showStatus("🔄 Formulário reiniciado", "info");
            
            if (navigator.vibrate) navigator.vibrate(50);
        });
    }

    if (elements.btnClear) {
        elements.btnClear.addEventListener("click", () => {
            console.log("🗑️ Limpando mensagem");
            
            if (elements.message) {
                elements.message.value = "";
                showStatus("🗑️ Mensagem limpa", "info");
            }
            
            if (navigator.vibrate) navigator.vibrate(30);
        });
    }

    if (elements.btnExit) {
        elements.btnExit.addEventListener("click", () => {
            console.log("🚪 Solicitando saída");
            
            if (confirm("Deseja realmente sair do sistema de emergência?")) {
                showStatus("👋 Até logo! Recarregando...", "info");
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        });
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
        showStatus("⚠️ Modo offline - verifique sua internet", "warning");
    } else {
        showStatus("✅ Sistema pronto - selecione uma situação", "success");
    }
});