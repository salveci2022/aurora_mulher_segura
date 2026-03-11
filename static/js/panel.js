// Painel Aurora - tempo real

let last=null

async function checkAlert(){

try{

const res=await fetch("/api/last_alert")

const data=await res.json()

if(!data.alert)return

if(last===data.alert.hora)return

last=data.alert.hora

showAlert(data.alert)

}catch(e){

console.log("Erro painel")

}

}

function showAlert(a){

const div=document.getElementById("alert")

if(!div)return

div.innerHTML=

"<b>Nome:</b>"+a.nome+"<br>"+
"<b>Situação:</b>"+a.situacao+"<br>"+
"<b>Mensagem:</b>"+a.mensagem+"<br>"+
"<b>Hora:</b>"+a.hora+"<br>"+
"<a target='_blank' href='https://maps.google.com/?q="+a.lat+","+a.lng+"'>Abrir mapa</a>"

const audio=new Audio("/static/siren.mp3")

audio.play()

}

setInterval(checkAlert,3000)