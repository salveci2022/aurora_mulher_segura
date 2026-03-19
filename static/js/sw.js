// ============================================
// AURORA — SERVICE WORKER v3.1
// Single consolidated SW (replaces service-worker.js + sw.js)
// ============================================

const CACHE_VERSION = "aurora-v3";
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;

const STATIC_ASSETS = [
    "/",
    "/offline",
    "/panic",
    "/static/css/style.css",
    "/static/js/panic.js",
    "/static/manifest.json"
];

// Install — cache static assets
self.addEventListener("install", event => {
    console.log("🛠️ Aurora SW v3.1 — instalando...");

    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                return Promise.all(
                    STATIC_ASSETS.map(url =>
                        cache.add(url).catch(err =>
                            console.warn(`⚠️ Não foi possível cachear ${url}:`, err)
                        )
                    )
                );
            })
            .then(() => {
                console.log("✅ Instalação concluída");
                return self.skipWaiting();
            })
    );
});

// Activate — remove ALL old caches
self.addEventListener("activate", event => {
    console.log("✅ Aurora SW v3.1 — ativado");

    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys.map(key => {
                    if (key !== STATIC_CACHE && key !== DYNAMIC_CACHE) {
                        console.log("🗑️ Removendo cache antigo:", key);
                        return caches.delete(key);
                    }
                })
            )
        ).then(() => self.clients.claim())
    );
});

// Fetch strategy
self.addEventListener("fetch", event => {
    const { request } = event;
    const url = new URL(request.url);

    // Never intercept API calls — always go to network
    if (url.pathname.startsWith("/api/")) return;

    // Non-GET requests pass through
    if (request.method !== "GET") return;

    // Navigation: Network-first, fall back to cache then offline page
    if (request.mode === "navigate") {
        event.respondWith(
            fetch(request)
                .then(response => {
                    const clone = response.clone();
                    caches.open(DYNAMIC_CACHE).then(cache => cache.put(request, clone));
                    return response;
                })
                .catch(() =>
                    caches.match(request)
                        .then(cached => cached || caches.match("/offline"))
                        .then(r => r || new Response(
                            "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Offline</title></head><body><h1>📴 Sem conexão</h1><p>Você está offline. Tente novamente.</p></body></html>",
                            { headers: { "Content-Type": "text/html" } }
                        ))
                )
        );
        return;
    }

    // Static assets: Cache-first, update in background
    event.respondWith(
        caches.match(request).then(cached => {
            const networkFetch = fetch(request).then(response => {
                if (response && response.status === 200) {
                    const clone = response.clone();
                    caches.open(STATIC_CACHE).then(cache => cache.put(request, clone));
                }
                return response;
            }).catch(() => null);

            return cached || networkFetch;
        })
    );
});

// Background sync for queued alerts
self.addEventListener("sync", event => {
    if (event.tag === "sync-alerts") {
        event.waitUntil(
            self.clients.matchAll().then(clients =>
                clients.forEach(client =>
                    client.postMessage({ type: "SYNC_ALERTS", timestamp: Date.now() })
                )
            )
        );
    }
});

// Message handler
self.addEventListener("message", event => {
    if (event.data && event.data.type === "SKIP_WAITING") {
        self.skipWaiting();
    }
});
