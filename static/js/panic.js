<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>Aurora Mulher Segura</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#7a00ff">
<link rel="icon" href="/static/icon-192.png">
<link rel="apple-touch-icon" href="/static/apple-touch-icon.png">

<style>
body{
 background:radial-gradient(circle at top,#3a0057,#0a0015);
 font-family:Arial;
 color:white;
 text-align:center;
}
.container{
 max-width:420px;
 margin:auto;
 padding:30px;
}
h1{color:#ff2fd4;}
button{
 width:100%;
 padding:22px;
 border:none;
 border-radius:14px;
 background:linear-gradient(45deg,#7a00ff,#ff2fd4);
 color:white;
 font-size:20px;
}
select,input{
 width:100%;
 padding:12px;
 margin-top:8px;
 border-radius:8px;
 border:none;
}
</style>
</head>

<body>
<div class="container">
  <h1>Aurora Mulher Segura</h1>

  <select id="trusted">
    {% for name in trusted %}
      <option>{{name}}</option>
    {% endfor %}
  </select>

  <input id="name" placeholder="Seu nome">
  <input id="situation" placeholder="Situação">
  <input id="message" placeholder="Mensagem opcional">

  <button onclick="send()">ATIVAR PÂNICO</button>
</div>

<script>
async function send(){
  if(!navigator.geolocation){
    alert("Seu celular/navegador não tem GPS disponível.");
    return;
  }

  navigator.geolocation.getCurrentPosition(async (pos)=>{
    try{
      await fetch("/api/send_alert",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
          name:document.getElementById("name").value,
          situation:document.getElementById("situation").value,
          message:document.getElementById("message").value,
          location:{
            lat:pos.coords.latitude,
            lon:pos.coords.longitude,
            accuracy_m:pos.coords.accuracy
          }
        })
      });
      alert("Alerta enviado!");
    }catch(e){
      alert("Falha ao enviar. Verifique a internet.");
    }
  }, ()=>{
    alert("Permita o acesso à localização para enviar o alerta.");
  }, { enableHighAccuracy:true, timeout:15000 });
}

// registra service worker (PWA)
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/static/sw.js").catch(()=>{});
}
</script>

</body>
</html>