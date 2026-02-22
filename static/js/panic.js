/* ===============================
   AURORA MULHER SEGURA - panic.js
   FIX DEFINITIVO (ANTI-TRAVA)
================================ */

document.addEventListener("DOMContentLoaded", () => {

  console.log("panic.js carregado com sucesso");

  const sosBtn = document.getElementById("sosBtn");
  const nameInput = document.getElementById("name");
  const messageInput = document.getElementById("message");
  const shareLoc = document.getElementById("shareLoc");
  const chips = document.querySelectorAll(".chip");
  const statusBox = document.getElementById("status");

  let selectedSituation = "";

  /* ===============================
     CHIPS
  ================================ */
  chips.forEach(chip => {
    chip.onclick = () => {
      chips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      selectedSituation = chip.innerText.trim();
    };
  });

  /* ===============================
     GEOLOCALIZAÇÃO
  ================================ */
  function getLocation() {
    return new Promise(resolve => {
      if (!shareLoc || !shareLoc.checked) {
        resolve(null);
        return;
      }

      if (!navigator.geolocation) {
        resolve(null);
        return;
      }

      navigator.geolocation.getCurrentPosition(
        pos => resolve({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude
        }),
        () => resolve(null),
        { enableHighAccuracy: true, timeout: 8000 }
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

    sosBtn.disabled = true;
    sosBtn.innerText = "ENVIANDO...";

    const location = await getLocation();

    const payload = {
      name: nameInput ? nameInput.value : "",
      situation: selectedSituation,
      message: messageInput ? messageInput.value : "",
      lat: location ? location.lat : null,
      lng: location ? location.lng : null
    };

    try {

      const res = await fetch("/api/send_alert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error();

      alert("✅ Alerta enviado com sucesso!");

    } catch (err) {
      alert("❌ Erro ao enviar alerta");
    }

    sosBtn.disabled = false;
    sosBtn.innerText = "SOS";
  }

  /* ===============================
     TOQUE E SEGURE
  ================================ */
  let holdTimer = null;

  sosBtn.addEventListener("mousedown", () => {
    holdTimer = setTimeout(sendAlert, 600);
  });

  sosBtn.addEventListener("mouseup", () => {
    clearTimeout(holdTimer);
  });

  sosBtn.addEventListener("mouseleave", () => {
    clearTimeout(holdTimer);
  });

  sosBtn.addEventListener("touchstart", e => {
    e.preventDefault();
    holdTimer = setTimeout(sendAlert, 600);
  });

  sosBtn.addEventListener("touchend", () => {
    clearTimeout(holdTimer);
  });

});