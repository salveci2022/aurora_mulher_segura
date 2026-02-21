const BACKENDS = [
  window.location.origin,
  "https://aurora-mulher-segura.onrender.com",
  "https://aurora-backup.fly.dev"
];

function qs(id){ return document.getElementById(id); }

function setStatus(msg){
  const el = qs("status");
  if(el) el.textContent = msg || "";
}

function getActiveSituation(){
  const chips = document.querySelectorAll("#chips .chip");
  for(const c of chips){
    if(c.classList.contains("active")) return c.textContent.trim();
  }
  return "";
}

async function postToBackends(path, payload){
  // tenta backend por backend (rápido e sem travar)
  for(const base of BACKENDS){
    try{
      const r = await fetch(base + path, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify(payload)
      });
      if(r.ok) return true;
    }catch(e){}
  }
  return false;
}

function getLocationOnce(timeoutMs=12000){
  return new Promise((resolve, reject)=>{
    if(!navigator.geolocation) return reject(new Error("Geolocalização indisponível."));
    const timer = setTimeout(()=>reject(new Error("Tempo esgotado ao obter GPS.")), timeoutMs);

    navigator.geolocation.getCurrentPosition(
      (pos)=>{
        clearTimeout(timer);
        resolve({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          acc: pos.coords.accuracy
        });
      },
      (err)=>{
        clearTimeout(timer);
        reject(err);
      },
      { enableHighAccuracy:true, timeout:timeoutMs, maximumAge:0 }
    );
  });
}

// Chips (seleção)
(function(){
  const chips = document.querySelectorAll("#chips .chip");
  chips.forEach(ch=>{
    ch.addEventListener("click", ()=>{
      chips.forEach(x=>x.classList.remove("active"));
      ch.classList.add("active");
    });
  });
})();

// Botões Reiniciar/Limpar/Sair
(function(){
  const btnRestart = qs("btnRestart");
  const btnClear   = qs("btnClear");
  const btnExit    = qs("btnExit");

  if(btnRestart) btnRestart.addEventListener("click", ()=>location.reload());

  if(btnClear) btnClear.addEventListener("click", ()=>{
    qs("name").value = "";
    qs("message").value = "";
    setStatus("Campos limpos.");
    setTimeout(()=>setStatus(""), 1200);
  });

  if(btnExit) btnExit.addEventListener("click", ()=>{
    // se estiver como PWA, volta pra tela inicial do app; no browser, abre página segura (em branco)
    try{ window.close(); }catch(e){}
    location.href = "/panic";
  });
})();

// SOS (toque e segure)
(function(){
  const btn = qs("sosBtn");
  if(!btn) return;

  let holdTimer = null;
  let sending = false;

  async function sendSOS(){
    if(sending) return;
    sending = true;

    const name = (qs("name").value || "").trim();
    const situation = getActiveSituation();
    const message = (qs("message").value || "").trim();
    const share = qs("shareLoc").checked;

    setStatus("Preparando alerta...");

    let loc = null;
    if(share){
      setStatus("Obtendo localização (GPS)...");
      try{
        loc = await getLocationOnce();
      }catch(e){
        // NÃO trava: só avisa e manda sem GPS
        loc = null;
        setStatus("Sem GPS (permissão/erro). Enviando sem localização...");
      }
    }

    const payload = {
      name,
      situation,
      message,
      lat: loc ? loc.lat : null,
      lng: loc ? loc.lng : null,
      accuracy: loc ? loc.acc : null,
      ts: new Date().toISOString()
    };

    setStatus("Enviando alerta...");
    const ok = await postToBackends("/api/send_alert", payload);

    if(ok){
      setStatus("✅ Alerta enviado com sucesso!");
    }else{
      setStatus("❌ Falha ao enviar. Verifique conexão/servidor.");
    }

    sending = false;
  }

  function startHold(){
    if(holdTimer || sending) return;
    setStatus("Segure... enviando em 1s");
    holdTimer = setTimeout(()=>{
      holdTimer = null;
      sendSOS();
    }, 1000);
  }

  function cancelHold(){
    if(holdTimer){
      clearTimeout(holdTimer);
      holdTimer = null;
      setStatus("");
    }
  }

  // Desktop
  btn.addEventListener("mousedown", startHold);
  btn.addEventListener("mouseup", cancelHold);
  btn.addEventListener("mouseleave", cancelHold);

  // Mobile
  btn.addEventListener("touchstart", (e)=>{ e.preventDefault(); startHold(); }, {passive:false});
  btn.addEventListener("touchend", (e)=>{ e.preventDefault(); cancelHold(); }, {passive:false});
})();