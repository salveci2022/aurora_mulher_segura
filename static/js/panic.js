// ============================================
// AURORA MULHER SEGURA - BOTÃO DE PÂNICO
// Versão: 2.0 - Alta disponibilidade com Failover
// ============================================

(() => {
    const $ = (id) => document.getElementById(id);
    const sos = $("sosBtn");
    const statusEl = $("status");
    const nameEl = $("name");
    const msgEl = $("message");
    const locToggle = $("shareLocation");
    const chips = Array.from(document.querySelectorAll("[data-situation]"));
    let holdTimer = null;
    let selectedSituation = "Violência física";
    
    // ===== CONFIGURAÇÃO DE FAILOVER =====
    const BACKENDS = [
        'https://aurora-mulher-segura.onrender.com',
        'https://aurora-backup.fly.dev'
    ];
    
    let activeBackend = 0;
    const cloudManagerUrl = window.location.origin; // Usa o mesmo domínio para reportar falhas
    
    // ===== BANCO DE DADOS LOCAL (IndexedDB) =====
    let db = null;
    const DB_NAME = "AuroraDB";
    const DB_VERSION = 1;
    const STORE_NAME = "alerts";

    // Inicializar banco de dados local
    function initDatabase() {
        return new Promise((resolve, reject) => {
            if (db) {
                resolve(db);
                return;
            }

            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onerror = (event) => {
                console.error("❌ Erro ao abrir banco local:", event.target.error);
                reject(event.target.error);
            };

            request.onsuccess = (event) => {
                db = event.target.result;
                console.log("✅ Banco local IndexedDB pronto");
                resolve(db);
            };

            request.onupgradeneeded = (event) => {
                const database = event.target.result;
                
                // Criar store para alertas
                if (!database.objectStoreNames.contains(STORE_NAME)) {
                    const store = database.createObjectStore(STORE_NAME, { 
                        keyPath: "id", 
                        autoIncrement: true 
                    });
                    
                    // Índices para busca
                    store.createIndex("timestamp", "timestamp", { unique: false });
                    store.createIndex("sent", "sent", { unique: false });
                    store.createIndex("emergency", "emergency", { unique: false });
                    
                    console.log("📦 Store de alertas criada");
                }
            };
        });
    }

    // Salvar alerta localmente
    async function saveAlertLocally(alertData) {
        try {
            await initDatabase();
            
            return new Promise((resolve, reject) => {
                const transaction = db.transaction([STORE_NAME], "readwrite");
                const store = transaction.objectStore(STORE_NAME);
                
                const alertToSave = {
                    ...alertData,
                    timestamp: new Date().toISOString(),
                    sent: false,
                    emergency: true,
                    retryCount: 0,
                    deviceInfo: {
                        userAgent: navigator.userAgent,
                        language: navigator.language,
                        platform: navigator.platform
                    }
                };

                const request = store.add(alertToSave);

                request.onsuccess = (event) => {
                    console.log("✅ Alerta salvo localmente. ID:", event.target.result);
                    statusEl.textContent = "📦 Alerta salvo no dispositivo";
                    resolve(event.target.result);
                };

                request.onerror = (event) => {
                    console.error("❌ Erro ao salvar localmente:", event.target.error);
                    // Fallback: localStorage
                    saveAlertToLocalStorage(alertData);
                    reject(event.target.error);
                };
            });
        } catch (error) {
            console.error("❌ Erro fatal no banco local:", error);
            // Fallback: salvar no localStorage
            saveAlertToLocalStorage(alertData);
        }
    }

    // Fallback: localStorage se IndexedDB falhar
    function saveAlertToLocalStorage(alertData) {
        try {
            const alerts = JSON.parse(localStorage.getItem('aurora_alerts') || '[]');
            alerts.push({
                ...alertData,
                timestamp: new Date().toISOString(),
                sent: false
            });
            localStorage.setItem('aurora_alerts', JSON.stringify(alerts));
            console.log("✅ Alerta salvo no localStorage (fallback)");
            statusEl.textContent = "📦 Alerta salvo (modo seguro)";
        } catch (e) {
            console.error("❌ Falha total no armazenamento:", e);
        }
    }

    // Marcar alerta como enviado
    async function markAsSent(alertId) {
        try {
            await initDatabase();
            
            return new Promise((resolve, reject) => {
                const transaction = db.transaction([STORE_NAME], "readwrite");
                const store = transaction.objectStore(STORE_NAME);
                
                const getRequest = store.get(alertId);

                getRequest.onsuccess = () => {
                    const alert = getRequest.result;
                    if (alert) {
                        alert.sent = true;
                        alert.sentAt = new Date().toISOString();
                        
                        const updateRequest = store.put(alert);
                        
                        updateRequest.onsuccess = () => {
                            console.log("✅ Alerta marcado como enviado:", alertId);
                            resolve();
                        };
                        
                        updateRequest.onerror = (error) => {
                            console.error("❌ Erro ao marcar como enviado:", error);
                            reject(error);
                        };
                    }
                };
            });
        } catch (error) {
            console.error("❌ Erro ao marcar como enviado:", error);
        }
    }

    // Tentar enviar alertas pendentes
    async function sendPendingAlerts() {
        try {
            await initDatabase();
            
            const transaction = db.transaction([STORE_NAME], "readonly");
            const store = transaction.objectStore(STORE_NAME);
            const index = store.index("sent");
            
            const request = index.getAll(IDBKeyRange.only(false));

            request.onsuccess = async () => {
                const pendingAlerts = request.result;
                
                if (pendingAlerts.length > 0) {
                    console.log(`📤 Tentando enviar ${pendingAlerts.length} alertas pendentes...`);
                    
                    for (const alert of pendingAlerts) {
                        try {
                            // Usa a função com failover para enviar pendentes
                            const result = await sendAlertWithFailover(alert);
                            
                            if (result.success) {
                                await markAsSent(alert.id);
                                console.log(`✅ Alerta pendente #${alert.id} enviado`);
                            } else {
                                alert.retryCount = (alert.retryCount || 0) + 1;
                                console.log(`⏳ Alerta #${alert.id} aguardando, tentativa ${alert.retryCount}`);
                            }
                        } catch (e) {
                            console.log("⏳ Sem conexão para enviar alertas pendentes");
                        }
                    }
                }
            };
        } catch (error) {
            console.error("❌ Erro ao processar alertas pendentes:", error);
        }
    }

    // Mostrar mensagem offline
    function showOfflineMessage() {
        // Criar elemento de aviso se não existir
        if (!document.getElementById('offline-warning')) {
            const warning = document.createElement('div');
            warning.id = 'offline-warning';
            warning.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 20px;
                right: 20px;
                background: #ff4fc8;
                color: white;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                font-weight: bold;
                z-index: 1000;
                animation: slideUp 0.3s ease;
                box-shadow: 0 0 20px rgba(255,79,200,0.5);
            `;
            warning.innerHTML = `
                <div style="font-size: 20px; margin-bottom: 5px;">🚨 MODO OFFLINE</div>
                <div style="font-size: 14px;">Seu alerta está SALVO no dispositivo</div>
                <div style="font-size: 12px; margin-top: 10px;">Será enviado quando a internet voltar</div>
                <div style="margin-top: 10px;">
                    <span style="background: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 5px;">📞 LIGUE 190 EM CASO DE EMERGÊNCIA</span>
                </div>
            `;
            document.body.appendChild(warning);
            
            setTimeout(() => {
                warning.style.animation = 'slideDown 0.3s ease';
                setTimeout(() => warning.remove(), 300);
            }, 8000);
        }
    }

    // ===== FUNÇÃO DE FAILOVER =====
    async function sendAlertWithFailover(alertData) {
        let lastError = null;
        
        // Tenta cada backend em ordem
        for (let i = 0; i < BACKENDS.length; i++) {
            const backendIndex = (activeBackend + i) % BACKENDS.length;
            const backend = BACKENDS[backendIndex];
            
            try {
                console.log(`📡 Tentando backend ${backendIndex}: ${backend}`);
                
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout
                
                const response = await fetch(`${backend}/api/send_alert`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-Failover-Attempt': i + 1,
                        'X-Client-Version': '2.0'
                    },
                    body: JSON.stringify(alertData),
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (response.ok) {
                    const result = await response.json();
                    console.log(`✅ Alerta enviado via ${backend}`);
                    
                    // Atualiza backend ativo
                    activeBackend = backendIndex;
                    
                    // Mostra qual backend usou
                    if (result.processed_by) {
                        console.log(`📍 Processado por: ${result.processed_by}`);
                    }
                    
                    return { success: true, backend, result };
                } else {
                    lastError = `HTTP ${response.status}`;
                    console.log(`⚠️ Backend ${backend} retornou erro: ${response.status}`);
                }
                
            } catch (error) {
                lastError = error.message;
                console.log(`❌ Backend ${backend} falhou: ${error.message}`);
                
                // Reporta falha para o backend (opcional)
                try {
                    await fetch(`${cloudManagerUrl}/api/report-failure`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            backend: backendIndex,
                            error: error.message 
                        })
                    });
                } catch (e) {
                    // Ignora erro no reporte
                }
            }
        }
        
        console.error('❌ Todos os backends falharam');
        return { success: false, error: lastError };
    }

    // ===== GEOLOCALIZAÇÃO DE ALTA PRECISÃO =====
    async function getLocation() {
        if (!locToggle || !locToggle.checked) {
            console.log("❌ Localização não autorizada");
            return null;
        }

        if (!navigator.geolocation) {
            console.log("❌ Geolocalização não suportada");
            return null;
        }

        statusEl.textContent = "🛰️ ATIVANDO GPS DE ALTA PRECISÃO...";
        statusEl.style.color = "#ff4fc8";

        return new Promise((resolve) => {
            let bestLocation = null;
            let bestAccuracy = Infinity;
            let attempts = 0;
            const maxAttempts = 5;
            const targetAccuracy = 5; // Queremos 5 metros ou menos

            function tryGetLocation() {
                attempts++;
                console.log(`📡 Tentativa ${attempts} de ${maxAttempts}`);

                const options = {
                    enableHighAccuracy: true,
                    timeout: 15000,
                    maximumAge: 0
                };

                navigator.geolocation.getCurrentPosition(
                    (pos) => {
                        const accuracy = pos.coords.accuracy;
                        console.log(`📍 Precisão: ${accuracy.toFixed(1)}m`);

                        if (accuracy < bestAccuracy) {
                            bestAccuracy = accuracy;
                            bestLocation = {
                                lat: pos.coords.latitude,
                                lon: pos.coords.longitude,
                                accuracy_m: accuracy,
                                timestamp: new Date().toISOString()
                            };
                        }

                        if (bestAccuracy <= targetAccuracy || attempts >= maxAttempts) {
                            statusEl.textContent = `📍 GPS: ${bestAccuracy.toFixed(1)}m`;
                            statusEl.style.color = "";
                            resolve(bestLocation);
                        } else {
                            statusEl.textContent = `⏳ Aguarde... ${bestAccuracy.toFixed(1)}m (ideal: ${targetAccuracy}m)`;
                            setTimeout(tryGetLocation, 2000);
                        }
                    },
                    (error) => {
                        console.log("❌ Erro GPS:", error.message);
                        
                        if (attempts < maxAttempts) {
                            setTimeout(tryGetLocation, 2000);
                        } else {
                            if (bestLocation) {
                                resolve(bestLocation);
                            } else {
                                statusEl.textContent = "❌ GPS indisponível";
                                resolve(null);
                            }
                        }
                    },
                    options
                );
            }

            tryGetLocation();
        });
    }

    // ===== FUNÇÃO PRINCIPAL DE ENVIO COM FAILOVER =====
    async function sendAlert() {
        try {
            console.log("%c🚨 INICIANDO ENVIO DE ALERTA COM FAILOVER", "color: #ff4fc8; font-size: 14px; font-weight: bold");
            
            const location = await getLocation();
            
            const alertData = {
                name: (nameEl.value || "").trim() || "Não informado",
                situation: selectedSituation,
                message: (msgEl.value || "").trim() || "",
                location: location,
                timestamp: new Date().toISOString(),
                appVersion: "2.0-failover"
            };

            console.log("📦 Dados do alerta:", alertData);

            // 1. Salva localmente SEMPRE (primeiro)
            const localId = await saveAlertLocally(alertData);
            
            // 2. Tenta enviar com failover
            statusEl.textContent = "📤 Enviando alerta...";
            const result = await sendAlertWithFailover(alertData);
            
            if (result.success) {
                await markAsSent(localId);
                
                if (location) {
                    statusEl.textContent = `✅ SOS ENVIADO! Precisão: ${Math.round(location.accuracy_m)}m (via ${result.backend})`;
                    statusEl.style.color = "#00ff00";
                } else {
                    statusEl.textContent = `✅ SOS ENVIADO! (via ${result.backend})`;
                    statusEl.style.color = "#00ff00";
                }
                
                console.log(`✅ Alerta #${result.result.id} enviado via ${result.backend}`);
                
                // Feedback visual de sucesso
                sos.style.backgroundColor = "rgba(0, 255, 0, 0.2)";
                
            } else {
                // Se todos falharam, alerta já está salvo localmente
                showOfflineMessage();
                statusEl.textContent = "📦 Alerta salvo (tentando novamente...)";
                statusEl.style.color = "#ffa500";
                
                // Agenda nova tentativa
                setTimeout(() => sendPendingAlerts(), 10000);
            }

            // Feedback visual no botão
            sos.style.transform = "scale(0.95)";
            setTimeout(() => {
                sos.style.transform = "";
            }, 200);

            setTimeout(() => {
                statusEl.textContent = "";
                statusEl.style.color = "";
                sos.style.backgroundColor = "";
            }, 5000);

        } catch (error) {
            console.error("❌ Erro crítico no envio:", error);
            statusEl.textContent = "❌ Erro no sistema";
            statusEl.style.color = "#ff0000";
            
            // Em caso de erro crítico, instruções de emergência
            alert("🚨 EMERGÊNCIA!\n\nLIGUE 190 IMEDIATAMENTE!\n\nSeu alerta será salvo e enviado quando possível.");
        }
    }

    // ===== EVENT LISTENERS =====
    function setSituation(v) {
        selectedSituation = v;
        chips.forEach(c => c.classList.toggle("active", c.dataset.situation === v));
    }

    function startHold(e) {
        e.preventDefault();
        statusEl.textContent = "⚠️ SOLTE PARA ENVIAR SOS...";
        statusEl.style.color = "#ff4fc8";
        sos.classList.add("holding");
        holdTimer = setTimeout(() => sendAlert(), 1200);
    }

    function endHold() {
        if (holdTimer) {
            clearTimeout(holdTimer);
            holdTimer = null;
        }
        sos.classList.remove("holding");
        if (statusEl.textContent.includes("SOLTE")) {
            statusEl.textContent = "";
            statusEl.style.color = "";
        }
    }

    // ===== SERVICE WORKER PARA OFFLINE =====
    async function registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/static/js/sw.js');
                console.log('✅ Service Worker registrado:', registration.scope);
                
                // Verificar sincronização em background
                if ('SyncManager' in window) {
                    registration.sync.register('sync-alerts');
                }
                
            } catch (error) {
                console.log('❌ Service Worker falhou:', error);
            }
        }
    }

    // ===== VERIFICAR CONEXÃO =====
    function checkConnection() {
        if (navigator.onLine) {
            console.log("✅ Dispositivo online");
            sendPendingAlerts(); // Tenta enviar pendentes quando online
        } else {
            console.log("📴 Dispositivo offline");
        }
    }

    // ===== INICIALIZAÇÃO =====
    async function init() {
        console.log("%c🚀 AURORA MULHER SEGURA v2.0 - COM FAILOVER", "color: #ff4fc8; font-size: 20px; font-weight: bold");
        console.log("📡 Backends configurados:", BACKENDS);
        
        // Inicializa banco de dados
        try {
            await initDatabase();
            console.log("✅ Sistema de armazenamento local pronto");
        } catch (e) {
            console.error("❌ Falha na inicialização do banco:", e);
        }
        
        // Registra Service Worker
        registerServiceWorker();
        
        // Verifica conexão inicial
        checkConnection();
        
        // Event listeners para conexão
        window.addEventListener('online', () => {
            console.log("✅ Conexão restabelecida");
            statusEl.textContent = "🌐 Online - enviando alertas...";
            sendPendingAlerts();
            setTimeout(() => {
                if (statusEl.textContent.includes("Online")) {
                    statusEl.textContent = "";
                }
            }, 3000);
        });
        
        window.addEventListener('offline', () => {
            console.log("📴 Conexão perdida");
            statusEl.textContent = "📴 Modo offline";
            setTimeout(() => {
                if (statusEl.textContent.includes("offline")) {
                    statusEl.textContent = "";
                }
            }, 3000);
        });
        
        // Configura situações
        chips.forEach(c => c.addEventListener("click", () => setSituation(c.dataset.situation)));
        setSituation(selectedSituation);
        
        // Event listeners do botão SOS
        sos.addEventListener("mousedown", startHold);
        sos.addEventListener("mouseup", endHold);
        sos.addEventListener("mouseleave", endHold);
        sos.addEventListener("touchstart", startHold, { passive: false });
        sos.addEventListener("touchend", endHold);
        sos.addEventListener("touchcancel", endHold);
        
        // Botões de controle
        $("btnClear")?.addEventListener("click", () => {
            nameEl.value = "";
            msgEl.value = "";
            if (locToggle) locToggle.checked = false;
            setSituation("Violência física");
            statusEl.textContent = "";
            statusEl.style.color = "";
        });

        $("btnReset")?.addEventListener("click", () => window.location.reload());
        $("btnExit")?.addEventListener("click", () => window.location.href = "/");
        
        // Instruções no console
        console.log("📋 INSTRUÇÕES DE SEGURANÇA:");
        console.log("1️⃣ Alerta é SALVO LOCALMENTE antes de enviar");
        console.log("2️⃣ Se um servidor falhar, tenta automaticamente o próximo");
        console.log("3️⃣ Se sem internet, fica pendente e envia automaticamente quando voltar");
        console.log("4️⃣ EMERGÊNCIA: Ligue 190 imediatamente");
        console.log("5️⃣ Precisão alvo: 5 metros");
    }

    // Inicia quando a página carregar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();