<script>

if ("serviceWorker" in navigator) {

navigator.serviceWorker.register("/static/service-worker.js")
.then(function(reg){

console.log("Service Worker registrado", reg);

})
.catch(function(err){

console.log("Erro no Service Worker", err);

});

}

</script>