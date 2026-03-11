// Aurora Mulher Segura
// Sistema SOS corrigido

document.addEventListener("DOMContentLoaded", function(){

let situation=null

const nameInput=document.getElementById("name")
const messageInput=document.getElementById("message")
const sos=document.getElementById("sosBtn")
const status=document.getElementById("status")

let location=null

// ====================
// GPS
// ====================

navigator.geolocation.watchPosition(pos=>{

location={
lat:pos.coords.latitude,
lng:pos.coords.longitude
}

console.log("GPS:",location)

})

// ====================
// Seleção de situação
// ====================

document.querySelectorAll(".chip").forEach(btn=>{

btn.addEventListener("click",function(){

document.querySelectorAll(".chip").forEach(b=>b.classList.remove("active"))

this.classList.add("active")

situation=this.dataset.value

})

})

// ====================
// Enviar alerta
// ====================

async function sendAlert(){

if(!situation){

status.innerText="Selecione a situação"
return

}

if(!location){

status.innerText="GPS não encontrado"
return

}

status.innerText="Enviando alerta..."

const data={

nome:nameInput.value || "Usuária",
situacao:situation,
mensagem:messageInput.value || "",
lat:location.lat,
lng:location.lng

}

try{

const res=await fetch("/api/alert",{

method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify(data)

})

const r=await res.json()

if(r.status==="ok"){

status.innerText="🚨 ALERTA ENVIADO"

navigator.vibrate?.([200,100,200])

}else{

status.innerText="Erro ao enviar"

}

}catch(e){

status.innerText="Erro de conexão"

}

}

// ====================
// Botão SOS
// ====================

if(sos){

sos.addEventListener("click",sendAlert)

}

})