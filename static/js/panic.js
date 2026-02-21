/* =========================================================
   AURORA MULHER SEGURA — panic.js (BLINDADO)
   - Chips não travam (tipo de ocorrência)
   - Envio com fallback de backends
   - Localização opcional
   - Funciona com botão SOS (click ou segurar, se existir)
========================================================= */

const BACKENDS = [
  window.location.origin,
  "https://aurora-mulher-segura.onrender.com",
  "https://aurora-backup.fly.dev"
];

const API_SEND = "/api/send_alert";
const API_LAST = "/api/last_alert";

let selectedSituation = "";

/* -------------------------
   Helpers
------------------------- */
function $(sel) { return document.querySelector(sel); }
function $all(sel) { return Array.from(document.querySelectorAll(sel)); }

function sleep(ms){ return new Promise(r => setTimeout(r, ms)); }

async function fetchWithTimeout(url, options = {}, timeoutMs = 9000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    return res;
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

      // pode ser json ou vazio
      const data = await res.json().catch(() => ({}));
      return { ok: true, base, data };
    } catch (e) {
      errors.push(`${base}${path} -> ${String(e)}`);
    }
  }
  return { ok: false, errors };
}

async function getLocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({
        lat: pos.coords.latitude,
        lng: pos.coords.longitude,
        accuracy: pos.coords.accuracy
      }),
      () => resolve(null),
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
    );
  });
}

function setStatus(msg, kind = "info") {
  const el = $("#status");
  if (!el) return;
  el.textContent = msg || "";
  el.classList.remove("ok", "err", "info");
  el.classList.add(kind);
}

/* =========================================================
   CHIPS (TIPO DE SITUAÇÃO) — BLINDADO
   Espera HTML assim:
   <button class="chip" data-situation="Violência física">...</button>
   OU apenas texto dentro do chip.
========================================================= */
function setupChips() {
  const chipEls = $all(".chip");
  if (!chipEls.length) return;

  // Se já tiver um chip ativo no HTML, usa ele
  const active = chipEls.find(c => c.classList.contains("active"));
  if (active) {
    selectedSituation = (active.dataset.situation || active.textContent || "").trim();
  }

  chipEls.forEach(chip => {
    chip.addEventListener("click", (ev) => {
      ev.preventDefault();

      chipEls.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");

      selectedSituation = (chip.dataset.situation || chip.textContent || "").trim();
    }, { passive: false });
  });
}

/* =========================================================
   ENVIO DO ALERTA
========================================================= */
async function sendAlert() {
  const nameEl = $("#name");
  const msgEl = $("#message");
  const shareLocEl = $("#shareLocation");

  const name = (nameEl?.value || "").trim();
  const message = (msgEl?.value || "").trim();
  const shareLocation = !!(shareLocEl?.checked);

  if (!selectedSituation) {
    setStatus("Selecione o tipo de situação.", "err");
    return;
  }

  setStatus("Enviando alerta…", "info");

  let loc = null;
  if (shareLocation) {
    setStatus("Obtendo localização…", "info");
    loc = await getLocation();
    if (!loc) {
      // não trava se GPS negar
      setStatus("Localização não disponível. Enviando sem GPS…", "info");
      await sleep(300);
    }
  }

  const payload = {
    name,
    situation: selectedSituation,
    message,
    lat: loc?.lat ?? null,
    lng: loc?.lng ?? null,
    accuracy: loc?.accuracy ?? null
  };

  const r = await postToBackends(API_SEND, payload);

  if (!r.ok) {
    console.error("Falha no envio:", r.errors);
    setStatus("Falha ao enviar. Tente novamente.", "err");
    return;
  }

  setStatus("✅ Alerta enviado com sucesso!", "ok");
}

/* =========================================================
   BOTÃO SOS — CLICK ou SEGURAR (se existir)
   - Se tiver #sosButton, usa ele
   - Se tiver #sendBtn, também funciona
========================================================= */
function setupSOS() {
  const sos = $("#sosButton");
  const sendBtn = $("#sendBtn");

  // Botão simples
  if (sendBtn) {
    sendBtn.addEventListener("click", (e) => {
      e.preventDefault();
      sendAlert();
    });
  }

  // SOS (segurar opcional)
  if (!sos) return;

  let holdTimer = null;
  let holding = false;

  const HOLD_MS = 650; // rápido, sem travar
  const startHold = (e) => {
    e.preventDefault();
    if (holding) return;
    holding = true;

    // se quiser animar via CSS, use class "holding"
    sos.classList.add("holding");

    holdTimer = setTimeout(async () => {
      await sendAlert();
      stopHold();
    }, HOLD_MS);
  };

  const stopHold = () => {
    holding = false;
    sos.classList.remove("holding");
    if (holdTimer) clearTimeout(holdTimer);
    holdTimer = null;
  };

  // mouse
  sos.addEventListener("mousedown", startHold);
  window.addEventListener("mouseup", stopHold);

  // touch
  sos.addEventListener("touchstart", startHold, { passive: false });
  window.addEventListener("touchend", stopHold);
  window.addEventListener("touchcancel", stopHold);

  // fallback: click normal também envia
  sos.addEventListener("click", (e) => {
    e.preventDefault();
    // se não segurou, envia no clique
    if (!holding) sendAlert();
  });
}

/* =========================================================
   INIT
========================================================= */
document.addEventListener("DOMContentLoaded", () => {
  setupChips();
  setupSOS();
});