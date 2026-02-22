/* =========================================================
   AURORA MULHER SEGURA — panic.js (ALINHADO AO SEU HTML)
   - Corrige travamento dos chips
   - Conecta SOS (id="sosBtn") e checkbox (id="shareLoc")
   - Reiniciar / Limpar / Sair
   - Envio com fallback de backends
========================================================= */

const BACKENDS = [
  window.location.origin,
  "https://aurora-mulher-segura.onrender.com",
  "https://aurora-backup.fly.dev"
];

const API_SEND = "/api/send_alert";

let selectedSituation = "";

// -------------------------
// Helpers
// -------------------------
function $(sel) { return document.querySelector(sel); }
function $all(sel) { return Array.from(document.querySelectorAll(sel)); }
function sleep(ms){ return new Promise(r => setTimeout(r, ms)); }

function setStatus(msg) {
  const el = $("#status");
  if (!el) return;
  el.textContent = msg || "";
}

async function fetchWithTimeout(url, options = {}, timeoutMs = 9000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(id);
  }
}

async function postToBackends(path, payload) {
  const errors = [];
  for (const base of BACKENDS) {
    try {
      const url = base.replace(/\/$/, "") + path;
      const res = await fetchWithTimeout(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }, 9000);

      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        errors.push(`${url} -> HTTP ${res.status} ${txt}`.trim());
        continue;
      }

      // pode retornar json ou vazio
      const data = await res.json().catch(() => ({}));
      return { ok: true, base, data };
    } catch (e) {
      errors.push(`${base}${path} -> ${String(e)}`);
    }
  }
  return { ok: false, errors };
}

function getLocationOnce(timeoutMs = 9000) {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve(null);

    let done = false;
    const timer = setTimeout(() => {
      if (done) return;
      done = true;
      resolve(null);
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
      () => {
        if (done) return;
        done = true;
        clearTimeout(timer);
        resolve(null);
      },
      { enableHighAccuracy: true, timeout: timeoutMs, maximumAge: 0 }
    );
  });
}

// -------------------------
// Chips (tipo de situação)
// -------------------------
function setupChips() {
  const chipEls = $all("#chips .chip");
  if (!chipEls.length) return;

  const active = chipEls.find(c => c.classList.contains("active"));
  if (active) selectedSituation = (active.textContent || "").trim();

  chipEls.forEach(chip => {
    chip.addEventListener("click", (ev) => {
      ev.preventDefault();
      chipEls.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      selectedSituation = (chip.textContent || "").trim();
    }, { passive: false });
  });
}

// -------------------------
// Ações (Reiniciar / Limpar / Sair)
// -------------------------
function setupMiniActions() {
  const btnRestart = $("#btnRestart");
  const btnClear = $("#btnClear");
  const btnExit = $("#btnExit");

  if (btnRestart) btnRestart.addEventListener("click", () => location.reload());

  if (btnClear) btnClear.addEventListener("click", () => {
    const nameEl = $("#name");
    const msgEl = $("#message");
    if (nameEl) nameEl.value = "";
    if (msgEl) msgEl.value = "";
    setStatus("Campos limpos.");
    setTimeout(() => setStatus(""), 900);
  });

  if (btnExit) btnExit.addEventListener("click", () => {
    // não dá pra “fechar” o browser com segurança; então só volta para /panic
    window.location.href = "/panic";
  });
}

// -------------------------
// Enviar alerta
// -------------------------
async function sendAlert() {
  const nameEl = $("#name");
  const msgEl = $("#message");
  const shareLocEl = $("#shareLoc"); // ✅ seu HTML usa shareLoc
  const sosBtn = $("#sosBtn");

  const name = (nameEl?.value || "").trim();
  const message = (msgEl?.value || "").trim();
  const shareLocation = !!(shareLocEl?.checked);

  if (!selectedSituation) {
    setStatus("Selecione o tipo de situação.");
    return;
  }

  if (sosBtn) sosBtn.disabled = true;
  setStatus("Enviando alerta…");

  let loc = null;
  if (shareLocation) {
    setStatus("Obtendo localização…");
    loc = await getLocationOnce(9000);
    if (!loc) {
      setStatus("Sem GPS (permissão/erro). Enviando sem localização…");
      await sleep(250);
    }
  }

  const payload = {
    name,
    situation: selectedSituation,
    message,
    lat: loc ? loc.lat : null,
    lng: loc ? loc.lng : null,
    accuracy: loc ? loc.accuracy : null
  };

  const r = await postToBackends(API_SEND, payload);

  if (!r.ok) {
    console.error("Falha no envio:", r.errors);
    setStatus("❌ Falha ao enviar. Tente novamente.");
    if (sosBtn) sosBtn.disabled = false;
    return;
  }

  setStatus("✅ Alerta enviado com sucesso!");
  if (sosBtn) sosBtn.disabled = false;
}

// -------------------------
// SOS: toque e segure (ou clique)
// -------------------------
function setupSOS() {
  const sos = $("#sosBtn"); // ✅ seu HTML usa sosBtn
  if (!sos) return;

  let holdTimer = null;

  const HOLD_MS = 650;

  const startHold = (e) => {
    e.preventDefault();
    if (holdTimer) return;
    setStatus("Segure… enviando");
    holdTimer = setTimeout(() => {
      holdTimer = null;
      sendAlert();
    }, HOLD_MS);
  };

  const cancelHold = () => {
    if (holdTimer) {
      clearTimeout(holdTimer);
      holdTimer = null;
      setStatus("");
    }
  };

  // mouse
  sos.addEventListener("mousedown", startHold);
  sos.addEventListener("mouseup", cancelHold);
  sos.addEventListener("mouseleave", cancelHold);

  // touch
  sos.addEventListener("touchstart", startHold, { passive: false });
  sos.addEventListener("touchend", cancelHold, { passive: false });
  sos.addEventListener("touchcancel", cancelHold, { passive: false });

  // fallback: clique também envia (rápido)
  sos.addEventListener("click", (e) => {
    e.preventDefault();
    if (!holdTimer) sendAlert();
  });
}

// -------------------------
// INIT
// -------------------------
document.addEventListener("DOMContentLoaded", () => {
  setupChips();
  setupMiniActions();
  setupSOS();
});