// =========================
// AURORA + DRIVER-SHIELD + TEMPO REAL
// =========================

let btn = document.getElementById("sos")
let tempoPressionado = null
let watchId = null

if(btn){
    btn.addEventListener("mousedown", iniciarPress)
    btn.addEventListener("mouseup", cancelarPress)

    btn.addEventListener("touchstart", iniciarPress)
    btn.addEventListener("touchend", cancelarPress)
}

function iniciarPress(){
    btn.classList.add("holding")

    tempoPressionado = setTimeout(() => {
        enviarAlerta()
    }, 2000)
}

function cancelarPress(){
    btn.classList.remove("holding")
    if(tempoPressionado) clearTimeout(tempoPressionado)
}

// =========================
// 🚨 ALERTA COM RASTREAMENTO
// =========================

function enviarAlerta(){

    let nome = document.getElementById("nome")?.value || "Não informado"
    let situacao = document.querySelector(".chip.active")?.innerText || "SOS"
    let mensagem = document.getElementById("mensagem")?.value || ""

    if(navigator.geolocation){

        watchId = navigator.geolocation.watchPosition(function(pos){

            let location = {
                lat: pos.coords.latitude,
                lng: pos.coords.longitude,
                accuracy: pos.coords.accuracy,
                source: "gps"
            }

            enviarParaServidor(nome, situacao, mensagem, location)

        }, function(){

            obterLocalizacaoIP(nome, situacao, mensagem)

        }, {
            enableHighAccuracy: true,
            maximumAge: 0,
            timeout: 5000
        })

    } else {
        obterLocalizacaoIP(nome, situacao, mensagem)
    }

    mostrarConfirmacao("🚨 Rastreamento iniciado...")
}

// =========================
// 🌐 FALLBACK IP
// =========================

function obterLocalizacaoIP(nome, situacao, mensagem){

    fetch("https://ipapi.co/json/")
    .then(res => res.json())
    .then(data => {

        let location = {
            lat: data.latitude,
            lng: data.longitude,
            accuracy: 5000,
            source: "ip"
        }

        enviarParaServidor(nome, situacao, mensagem, location)

    })
    .catch(() => {
        enviarParaServidor(nome, situacao, mensagem, null)
    })
}

// =========================
// 📡 ENVIO
// =========================

function enviarParaServidor(nome, situacao, mensagem, location){

    const payload = {
        name: nome,
        situation: situacao,
        message: mensagem,

        location: location,

        lat: location ? location.lat : null,
        lng: location ? location.lng : null,
        accuracy: location ? location.accuracy : null,

        locationSource: location?.source || 'none',
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent
    }

    fetch("/api/send_alert", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(() => {
        console.log("Localização enviada")
    })
    .catch(err => {
        console.error("Erro:", err)
    })
}

// =========================
// FEEDBACK
// =========================

function mostrarConfirmacao(msg){

    let el = document.getElementById("status")

    if(!el){
        el = document.createElement("div")
        el.id = "status"
        el.style.marginTop = "10px"
        document.body.appendChild(el)
    }

    el.innerText = msg

    setTimeout(() => el.innerText = "", 4000)
}

// =========================
// CHIPS
// =========================

document.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
        document.querySelectorAll(".chip").forEach(c => c.classList.remove("active"))
        chip.classList.add("active")
    })
})