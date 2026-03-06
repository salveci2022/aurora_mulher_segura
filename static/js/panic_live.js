let rastreando = false;

function iniciarRastreamento(){

if(rastreando) return;

rastreando = true;

setInterval(()=>{

navigator.geolocation.getCurrentPosition(pos=>{

fetch("/api/send_location",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({

lat:pos.coords.latitude,
lng:pos.coords.longitude,
accuracy:pos.coords.accuracy

})

});

});

},5000);

}