const CACHE_NAME = "aurora-cache-v1";

const FILES_TO_CACHE = [
    "/",
    "/panic",
    "/static/css/style.css",
    "/static/js/panic.js",
    "/static/img/icon-192.png",
    "/static/img/icon-512.png",
    "/offline"
];

self.addEventListener("install", event => {
    console.log("🌸 Service Worker instalado");

    event.waitUntil(
        caches.open(CACHE_NAME)
        .then(cache => cache.addAll(FILES_TO_CACHE))
    );

    self.skipWaiting();
});

self.addEventListener("activate", event => {
    console.log("🌸 Service Worker ativo");

    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.map(key => {
                    if (key !== CACHE_NAME) {
                        return caches.delete(key);
                    }
                })
            );
        })
    );

    self.clients.claim();
});

self.addEventListener("fetch", event => {

    if (event.request.method !== "GET") return;

    event.respondWith(

        caches.match(event.request)
        .then(response => {

            if (response) {
                return response;
            }

            return fetch(event.request)
            .then(networkResponse => {

                const cloned = networkResponse.clone();

                caches.open(CACHE_NAME)
                .then(cache => cache.put(event.request, cloned));

                return networkResponse;

            }).catch(() => {

                if (event.request.destination === "document") {
                    return caches.match("/offline");
                }

            });

        })

    );

});