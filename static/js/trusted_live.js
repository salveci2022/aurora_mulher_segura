let map;
let marker;

const sirene = new Audio("/static/siren.mp3");

function iniciarMapa(){

fetch("/api/last_alert")

.then(r=>r.json())

.then(data=>{

if(!data.last) return;

let lat = data.last.location.lat;
let lng = data.last.location.lng;

map = new google.maps.Map(document.getElementById("map"),{

zoom:16,
center:{lat:lat,lng:lng}

});

marker = new google.maps.Marker({

position:{lat:lat,lng:lng},
map:map

});

sirene.play();

document.getElementById("alerta").classList.add("alerta_ativo");

});

}