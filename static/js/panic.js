// ================================
// AURORA MULHER SEGURA - PANIC.JS
// ================================

// Ordem de tentativa de envio
const BACKENDS = [
  window.location.origin,                 // servidor atual
  'https://aurora-mulher-segura.onrender.com',
  'https://aurora-backup.fly.dev'
];

let sending = false;

// -------------------------------
// Helpers
// -------------------------------

function qs(id) {
  return document.getElementById(id);
}

function setStatus(msg) {
  const el = qs("status");
  if (el) el.innerText = msg;
}

function getSituation() {
  const active = document.querySelector(".chip.active");
  return active ? active.dataset.situation : "";
}

async function postToBackend(path, payload) {
  for (let base of BACKENDS) {
    try {
      const res = await fetch(base + path, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        return true;
      }
    } catch (e) {
      console.log("Falhou em:", base);
    }
  }
  return false;
}

// -------------------------------
// GEOLOCATION
// -------------------------------

function getLocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve({ lat: null, lng: null });
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        resolve({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude
        });
      },
      () => resolve({ lat: null, lng: null }),
      { enableHighAccuracy: true, timeout: 10000 }
    );
  });
}

// -------------------------------
// SEND ALERT
// -------------------------------

async function sendAlert() {
  if (sending) return;
  sending = true;

  setStatus("Enviando alerta...");

  const name = qs("name")?.value || "";
  const message = qs("message")?.value || "";
  const situation = getSituation();
  const shareLocation = qs("shareLocation")?.checked || false;

  let lat = null;
  let lng = null;

  if (shareLocation) {
    const loc = await getLocation();
    lat = loc.lat;
    lng = loc.lng;
  }

  const payload = {
    name,
    message,
    situation,
    lat,
    lng
  };

  const ok = await postToBackend("/api/send_alert", payload);

  if (ok) {
    setStatus("Alerta enviado com sucesso!");
  } else {
    setStatus("Falha ao enviar alerta.");
  }

  sending = false;
}

// -------------------------------
// EVENTS
// -------------------------------

document.addEventListener("DOMContentLoaded", () => {

  // Chips de situação
  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
    });
  });

  // Botão SOS
  const sosBtn = qs("sosBtn");
  if (sosBtn) {
    sosBtn.addEventListener("click", sendAlert);
  }

});