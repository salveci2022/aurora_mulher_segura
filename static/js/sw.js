// ============================================
// AURORA - SERVICE WORKER (MODO OFFLINE)
// ============================================

const CACHE_NAME = 'aurora-cache-v1';
const urlsToCache = [
    '/',
    '/panic',
    '/static/css/style.css',
    '/static/js/panic.js',
    '/static/audio/sirene.mp3',
    '/offline.html'
];

// Instalar Service Worker
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

// Ativar Service Worker
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

// Interceptar requisições
self.addEventListener('fetch', event => {
    // Não fazer cache de APIs
    if (event.request.url.includes('/api/')) {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then(response => {
                // Se conseguiu baixar, atualiza o cache
                if (response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, responseClone);
                    });
                }
                return response;
            })
            .catch(() => {
                // Se falhou (offline), tenta pegar do cache
                return caches.match(event.request).then(response => {
                    if (response) {
                        console.log('📴 Modo offline - servindo do cache:', event.request.url);
                        return response;
                    }
                    // Se não tiver no cache, mostra página offline
                    if (event.request.mode === 'navigate') {
                        return caches.match('/offline.html');
                    }
                });
            })
    );
});

// Sincronização em background
self.addEventListener('sync', event => {
    if (event.tag === 'sync-alerts') {
        console.log('🔄 Sincronizando alertas pendentes...');
        event.waitUntil(syncAlerts());
    }
});

// Função para sincronizar alertas
async function syncAlerts() {
    try {
        const clients = await self.clients.matchAll();
        clients.forEach(client => {
            client.postMessage({
                type: 'SYNC_ALERTS'
            });
        });
    } catch (error) {
        console.error('❌ Erro na sincronização:', error);
    }
}