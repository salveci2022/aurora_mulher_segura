/* ===============================
   AURORA MULHER SEGURA - panic.js
   FIX DEFINITIVO (ANTI-TRAVA)
================================ */

document.addEventListener("DOMContentLoaded", () => {

  console.log("panic.js carregado com sucesso");

  // Verificar se todos os elementos existem antes de prosseguir
  const sosBtn = document.getElementById("sosBtn");
  if (!sosBtn) {
    console.error("Botão SOS não encontrado!");
    return; // Para a execução se não encontrar o botão
  }

  const nameInput = document.getElementById("name");
  const messageInput = document.getElementById("message");
  const shareLoc = document.getElementById("shareLoc");
  const statusBox = document.getElementById("status");
  
  // Verificar se os chips existem
  const chips = document.querySelectorAll(".chip");
  
  let selectedSituation = "";

  /* ===============================
     CHIPS
  ================================ */
  if (chips.length > 0) {
    chips.forEach(chip => {
      chip.onclick = () => {
        chips.forEach(c => c.classList.remove("active"));
        chip.classList.add("active");
        selectedSituation = chip.innerText.trim();
      };
    });
  } else {
    console.warn("Nenhum chip encontrado");
  }

  /* ===============================
     GEOLOCALIZAÇÃO
  ================================ */
  function getLocation() {
    return new Promise(resolve => {
      // Verificar se o checkbox existe e está marcado
      if (!shareLoc || !shareLoc.checked) {
        resolve(null);
        return;
      }

      if (!navigator.geolocation) {
        console.warn("Geolocalização não suportada");
        resolve(null);
        return;
      }

      navigator.geolocation.getCurrentPosition(
        pos => resolve({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude
        }),
        err => {
          console.warn("Erro ao obter localização:", err.message);
          resolve(null);
        },
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
      );
    });
  }

  /* ===============================
     ENVIAR ALERTA
  ================================ */
  async function sendAlert() {

    if (!selectedSituation) {
      alert("Selecione o tipo de situação");
      return;
    }

    // Desabilitar botão durante envio
    sosBtn.disabled = true;
    const originalText = sosBtn.innerText;
    sosBtn.innerText = "ENVIANDO...";

    try {
      const location = await getLocation();

      const payload = {
        name: nameInput ? nameInput.value || "" : "",
        situation: selectedSituation,
        message: messageInput ? messageInput.value || "" : "",
        lat: location ? location.lat : null,
        lng: location ? location.lng : null
      };

      console.log("Enviando payload:", payload);

      const res = await fetch("/api/send_alert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`HTTP ${res.status}: ${errorText}`);
      }

      alert("✅ Alerta enviado com sucesso!");

    } catch (err) {
      console.error("Erro detalhado:", err);
      alert("❌ Erro ao enviar alerta. Verifique sua conexão.");
    } finally {
      // Restaurar botão em qualquer caso (sucesso ou erro)
      sosBtn.disabled = false;
      sosBtn.innerText = originalText;
    }
  }

  /* ===============================
     TOQUE E SEGURE
  ================================ */
  let holdTimer = null;
  const HOLD_DURATION = 600; // ms

  // Limpar timer anterior se existir
  function clearHoldTimer() {
    if (holdTimer) {
      clearTimeout(holdTimer);
      holdTimer = null;
    }
  }

  // Event listeners com tratamento de erros
  sosBtn.addEventListener("mousedown", () => {
    clearHoldTimer();
    holdTimer = setTimeout(() => {
      sendAlert().catch(console.error);
    }, HOLD_DURATION);
  });

  sosBtn.addEventListener("mouseup", clearHoldTimer);
  sosBtn.addEventListener("mouseleave", clearHoldTimer);

  // Touch events para mobile
  sosBtn.addEventListener("touchstart", e => {
    e.preventDefault();
    clearHoldTimer();
    holdTimer = setTimeout(() => {
      sendAlert().catch(console.error);
    }, HOLD_DURATION);
  });

  sosBtn.addEventListener("touchend", clearHoldTimer);
  sosBtn.addEventListener("touchcancel", clearHoldTimer);

  console.log("panic.js inicializado com sucesso");
});