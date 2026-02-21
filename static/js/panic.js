const statusEl = document.getElementById("status");
const chipsEl = document.getElementById("chips");
const sosBtn = document.getElementById("sosBtn");

function setStatus(msg, type = "ok") {
  if (!statusEl) return;
  statusEl.textContent = msg || "";
  statusEl.className = "status " + (type === "err" ? "status-err" : "status-ok");
}

function getSelectedSituation() {
  const active = document.querySelector(".chip.active");
  return active ? active.dataset.value : "";
}

function selectChip(btn) {
  document.querySelectorAll(".chip").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
}

if (chipsEl) {
  chipsEl.addEventListener("click", (e) => {
    const btn = e.target.closest(".chip");
    if (!btn) return;
    selectChip(btn);
  });
}

function getLocationOnce(timeoutMs = 9000) {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) return reject(new Error("Geolocalização não suportada."));
    let done = false;

    const timer = setTimeout(() => {
      if (done) return;
      done = true;
      reject(new Error("Tempo limite para obter localização."));
    }, timeoutMs);

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        if (done) return;
        done = true;
        clearTimeout(timer);
        resolve({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: pos.coords.accuracy
        });
      },
      (err) => {
        if (done) return;
        done = true;
        clearTimeout(timer);
        reject(err);
      },
      { enableHighAccuracy: true, timeout: timeoutMs, maximumAge: 0 }
    );
  });
}

async function sendAlert(payload) {
  const res = await fetch("/api/send_alert", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!res.ok) throw new Error("Falha ao enviar alerta (HTTP " + res.status + ")");
  return res.json().catch(() => ({}));
}

async function handleSOS() {
  try {
    sosBtn.disabled = true;
    setStatus("Enviando alerta...", "ok");

    const name = (document.getElementById("name")?.value || "").trim();
    const message = (document.getElementById("message")?.value || "").trim();
    const situation = getSelectedSituation();
    const share = document.getElementById("share_location")?.checked;

    let loc = null;
    if (share) {
      try {
        loc = await getLocationOnce();
      } catch (e) {
        // Se não pegar GPS, ainda assim envia sem localização
        loc = null;
      }
    }

    const payload = {
      name,
      situation,
      message,
      lat: loc ? loc.lat : null,
      lng: loc ? loc.lng : null,
      accuracy: loc ? loc.accuracy : null
    };

    await sendAlert(payload);
    setStatus("✅ Alerta enviado com sucesso!", "ok");
  } catch (e) {
    setStatus("❌ Erro: " + (e?.message || "falha ao enviar"), "err");
  } finally {
    sosBtn.disabled = false;
  }
}

if (sosBtn) {
  sosBtn.addEventListener("click", handleSOS);
}