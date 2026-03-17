let sosBtn = document.getElementById("sosBtn")
let statusMsg = document.getElementById("statusMsg")
let gpsStatus = document.getElementById("gpsStatus")

let segurando = false
let timer = null
let localizacaoAtual = null


/* ===============================
CAPTURAR GPS
=============================== */

function capturarGPS(){

if(!navigator.geolocation){

gpsStatus.innerText = "GPS não suportado"

return

}

navigator.geolocation.getCurrentPosition(function(pos){

localizacaoAtual = {

lat: pos.coords.latitude,
lng: pos.coords.longitude

}

gpsStatus.innerText = "📍 Localização capturada"

}, function(){

gpsStatus.innerText = "Erro ao capturar GPS"

},{

enableHighAccuracy:true,
timeout:10000

})

}

capturarGPS()


/* ===============================
SITUAÇÃO SELECIONADA
=============================== */

function getSituacao(){

let ativo = document.querySelector(".chip.active")

if(!ativo) return "Emergência"

return ativo.dataset.value

}


/* ===============================
ENVIAR ALERTA
=============================== */

function enviarAlerta(){

let nome = document.getElementById("nomeInput").value || "Usuária"

let mensagem = document.getElementById("mensagemInput").value || ""

let situacao = getSituacao()

let payload = {

nome: nome,
mensagem: mensagem,
situacao: situacao,
localizacao: localizacaoAtual

}

fetch("/api/alert",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body: JSON.stringify(payload)

})
.then(res => res.json())
.then(data =>{

statusMsg.innerText = "🚨 ALERTA ENVIADO"

})
.catch(err =>{

statusMsg.innerText = "Erro ao enviar alerta"

})

}


/* ===============================
BOTÃO SEGURAR SOS
=============================== */

sosBtn.addEventListener("mousedown",function(){

segurando = true

timer = setTimeout(function(){

if(segurando){

enviarAlerta()

}

},1000)

})


sosBtn.addEventListener("mouseup",function(){

segurando = false

clearTimeout(timer)

})


sosBtn.addEventListener("mouseleave",function(){

segurando = false

clearTimeout(timer)

})


/* ===============================
MOBILE TOUCH
=============================== */

sosBtn.addEventListener("touchstart",function(){

segurando = true

timer = setTimeout(function(){

if(segurando){

enviarAlerta()

}

},1000)

})


sosBtn.addEventListener("touchend",function(){

segurando = false

clearTimeout(timer)

})


/* ===============================
ATUALIZAR GPS A CADA 20s
=============================== */

setInterval(function(){

capturarGPS()

},20000)