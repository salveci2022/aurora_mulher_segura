(() => {
  const $ = (id) => document.getElementById(id);
  const sos = $("sosBtn");
  const statusEl = $("status");
  const nameEl = $("name");
  const msgEl = $("message");
  const locToggle = $("shareLocation");
  const chips = Array.from(document.querySelectorAll("[data-situation]"));
  let holdTimer = null;
  let watchId = null; // Para monitoramento contínuo
  let selectedSituation = "Violência física";

  function setSituation(v) {
    selectedSituation = v;
    chips.forEach(c => c.classList.toggle("active", c.dataset.situation === v));
  }
  chips.forEach(c => c.addEventListener("click", () => setSituation(c.dataset.situation)));
  setSituation(selectedSituation);

  async function getLocationHighPrecision() {
    if (!locToggle || !locToggle.checked) return null;
    if (!navigator.geolocation) return null;

    statusEl.textContent = "🛰️ ATIVANDO GPS DE ALTA PRECISÃO...";
    statusEl.style.color = "#ff4fc8";

    return new Promise((resolve) => {
      let bestLocation = null;
      let bestAccuracy = Infinity;
      let attempts = 0;
      const maxAttempts = 8; // Mais tentativas
      const targetAccuracy = 5; // Queremos 5 metros ou menos
      
      // Para qualquer watch anterior
      if (watchId) navigator.geolocation.clearWatch(watchId);
      
      // Usar watchPosition para monitoramento contínuo até atingir precisão
      watchId = navigator.geolocation.watchPosition(
        (pos) => {
          const accuracy = pos.coords.accuracy;
          console.log(`📍 Precisão: ${accuracy.toFixed(1)}m`);
          
          // Guarda a melhor localização
          if (accuracy < bestAccuracy) {
            bestAccuracy = accuracy;
            bestLocation = {
              lat: pos.coords.latitude,
              lon: pos.coords.longitude,
              accuracy_m: accuracy,
              timestamp: new Date().toISOString()
            };
            
            statusEl.textContent = `📡 GPS: ${bestAccuracy.toFixed(1)}m (meta: ${targetAccuracy}m)`;
            
            // Se atingiu a meta ou já temos uma precisão boa
            if (bestAccuracy <= targetAccuracy) {
              console.log(`✅ PRECISÃO IDEAL: ${bestAccuracy.toFixed(1)}m`);
              navigator.geolocation.clearWatch(watchId);
              watchId = null;
              statusEl.textContent = `📍 GPS FINAL: ${bestAccuracy.toFixed(1)}m`;
              resolve(bestLocation);
            }
          }
          
          attempts++;
          // Se já tentou muitas vezes, pega a melhor disponível
          if (attempts >= maxAttempts && bestLocation) {
            console.log(`⏱️ Máximo de tentativas. Melhor: ${bestAccuracy.toFixed(1)}m`);
            navigator.geolocation.clearWatch(watchId);
            watchId = null;
            statusEl.textContent = `📍 GPS: ${bestAccuracy.toFixed(1)}m`;
            resolve(bestLocation);
          }
        },
        (error) => {
          console.log("❌ Erro GPS:", error.message);
          if (error.code === 1) { // PERMISSION_DENIED
            statusEl.textContent = "❌ Permita localização no navegador";
          }
          
          if (bestLocation) {
            // Se já temos alguma localização, usa ela
            navigator.geolocation.clearWatch(watchId);
            watchId = null;
            resolve(bestLocation);
          } else {
            resolve(null);
          }
        },
        {
          enableHighAccuracy: true,  // FORÇA GPS
          timeout: 15000,            // 15 segundos
          maximumAge: 0               // Sem cache
        }
      );
      
      // Timeout geral (30 segundos)
      setTimeout(() => {
        if (watchId) {
          navigator.geolocation.clearWatch(watchId);
          watchId = null;
          if (bestLocation) {
            resolve(bestLocation);
          } else {
            resolve(null);
          }
        }
      }, 30000);
    });
  }

  function startHold(e) {
    e.preventDefault();
    statusEl.textContent = "⚠️ MANTENHA PARA ENVIAR SOS...";
    sos.classList.add("holding");
    holdTimer = setTimeout(() => sendAlert(), 1200);
  }

  function endHold() {
    if (holdTimer) {
      clearTimeout(holdTimer);
      holdTimer = null;
    }
    sos.classList.remove("holding");
    if (statusEl.textContent.includes("MANTENHA")) {
      statusEl.textContent = "";
    }
  }

  async function sendAlert() {
    try {
      const location = await getLocationHighPrecision();

      const payload = {
        name: (nameEl.value || "").trim() || "Não informado",
        situation: selectedSituation,
        message: (msgEl.value || "").trim() || "",
        location: location
      };

      console.log("📦 Enviando:", payload);

      const res = await fetch("/api/send_alert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (data.ok) {
        if (location) {
          statusEl.textContent = `✅ SOS ENVIADO! Precisão: ${Math.round(location.accuracy_m)}m`;
          if (location.accuracy_m <= 5) {
            statusEl.style.color = "#00ff00"; // Verde para excelente
          } else if (location.accuracy_m <= 10) {
            statusEl.style.color = "#ffff00"; // Amarelo para boa
          } else {
            statusEl.style.color = "#ff4fc8"; // Rosa para aceitável
          }
        } else {
          statusEl.textContent = "✅ SOS ENVIADO (sem localização)";
        }
      }

      setTimeout(() => {
        statusEl.textContent = "";
        statusEl.style.color = "";
      }, 5000);

    } catch (e) {
      console.error("❌ Erro:", e);
      statusEl.textContent = "❌ Erro de conexão";
      setTimeout(() => {
        statusEl.textContent = "";
        statusEl.style.color = "";
      }, 3000);
    }
  }

  // Event listeners
  sos.addEventListener("mousedown", startHold);
  sos.addEventListener("mouseup", endHold);
  sos.addEventListener("mouseleave", endHold);
  sos.addEventListener("touchstart", startHold, { passive: false });
  sos.addEventListener("touchend", endHold);
  sos.addEventListener("touchcancel", endHold);

  // Botões
  $("btnClear")?.addEventListener("click", () => {
    nameEl.value = "";
    msgEl.value = "";
    if (locToggle) locToggle.checked = false;
    setSituation("Violência física");
    statusEl.textContent = "";
    statusEl.style.color = "";
    if (watchId) navigator.geolocation.clearWatch(watchId);
  });

  $("btnReset")?.addEventListener("click", () => window.location.reload());
  $("btnExit")?.addEventListener("click", () => window.location.href = "/");

  console.log("📋 GPS ALTA PRECISÃO ATIVADO");
})();