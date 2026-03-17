const sireneBtn = document.getElementById("sireneBtn")

const audio = new Audio("/static/sirene.mp3")

let map
let marker

function iniciarMapa(lat,lng){

    const pos = {lat:lat,lng:lng}

    map = new google.maps.Map(document.getElementById("map"),{

        zoom:18,
        center:pos

    })

    marker = new google.maps.Marker({

        position:pos,
        map:map

    })

}

function atualizarMapa(lat,lng){

    const pos = {lat:lat,lng:lng}

    map.setCenter(pos)

    marker.setPosition(pos)

}

function tocarSirene(){

    sireneBtn.classList.add("sirene-ativa")

    audio.play()

}

function verificarAlertas(){

    fetch("/api/last_alert")

    .then(r=>r.json())

    .then(data=>{

        if(!data.alerta) return

        tocarSirene()

        document.getElementById("nome").innerText =
        "Pessoa: " + data.nome

        document.getElementById("situacao").innerText =
        "Situação: " + data.situacao

        const lat = parseFloat(data.lat)
        const lng = parseFloat(data.lng)

        if(!map){

            iniciarMapa(lat,lng)

        }else{

            atualizarMapa(lat,lng)

        }

    })

}

setInterval(verificarAlertas,5000)



function limpar(){

location.reload()

}

function reenviar(){

alert("Reenviar alerta")

}

function sair(){

window.location.href="/"

}