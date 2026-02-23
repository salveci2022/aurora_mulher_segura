const CACHE_NAME = 'aurora-cache-v1';
const urlsToCache = [
    '/',
    '/panic',
    '/static/css/style.css',
    '/static/js/panic.js'
];

self.addEventListener('install', event => {
    console.log('🛠️ Instalando Service Worker...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('📦 Arquivos em cache:', urlsToCache);
                return cache.addAll(urlsToCache);
            })
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', event => {
    console.log('✅ Service Worker ativado');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('🗑️ Removendo cache antigo:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', event => {
    if (event.request.url.includes('/api/')) {
        return;
    }
    
    event.respondWith(
        fetch(event.request)
            .then(response => {
                if (response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, responseClone);
                    });
                }
                return response;
            })
            .catch(() => {
                return caches.match(event.request).then(response => {
                    if (response) {
                        console.log('📴 Modo offline - servindo do cache:', event.request.url);
                        return response;
                    }
                    if (event.request.mode === 'navigate') {
                        return caches.match('/offline.html');
                    }
                });
            })
    );
});