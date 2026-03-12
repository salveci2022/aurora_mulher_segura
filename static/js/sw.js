// ============================================
// AURORA - SERVICE WORKER (MODO OFFLINE)
// VERSÃO 2.0 - CORRIGIDA E OTIMIZADA
// ============================================

const CACHE_NAME = 'aurora-cache-v2';
const STATIC_CACHE = 'aurora-static-v2';

const urlsToCache = [
    '/',
    '/offline',
    '/panic',
    '/static/css/style.css',
    '/static/js/panic.js',
    '/static/js/sw.js',
    '/static/manifest.json'
];

// Instalação - cache dos arquivos estáticos
self.addEventListener('install', event => {
    console.log('🛠️ Instalando Service Worker v2...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('📦 Cacheando arquivos estáticos...');
                return cache.addAll(urlsToCache).catch(error => {
                    console.error('❌ Erro ao cachear:', error);
                    return Promise.all(
                        urlsToCache.map(url => 
                            cache.add(url).catch(err => 
                                console.warn(`⚠️ Não foi possível cachear ${url}:`, err)
                            )
                        )
                    );
                });
            })
            .then(() => {
                console.log('✅ Instalação concluída');
                return self.skipWaiting();
            })
    );
});

// Ativação - limpa caches antigos
self.addEventListener('activate', event => {
    console.log('✅ Service Worker ativado');
    
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== STATIC_CACHE && cacheName !== CACHE_NAME) {
                        console.log('🗑️ Removendo cache antigo:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('✅ Service Worker pronto para controle');
            return self.clients.claim();
        })
    );
});

// Estratégia de cache
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Ignora requisições de API
    if (url.pathname.startsWith('/api/')) {
        return;
    }
    
    // Para navegação (páginas HTML)
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request)
                .then(response => {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(request, responseClone);
                    });
                    return response;
                })
                .catch(() => {
                    return caches.match(request).then(response => {
                        if (response) {
                            return response;
                        }
                        return caches.match('/offline').then(offlineResponse => {
                            if (offlineResponse) {
                                return offlineResponse;
                            }
                            return new Response(
                                '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Offline</title></head><body><h1>📴 Offline</h1><p>Sem conexão com internet</p></body></html>',
                                { headers: { 'Content-Type': 'text/html' } }
                            );
                        });
                    });
                })
        );
        return;
    }
    
    // Para arquivos estáticos
    event.respondWith(
        caches.match(request)
            .then(response => {
                if (response) {
                    fetch(request)
                        .then(networkResponse => {
                            if (networkResponse && networkResponse.status === 200) {
                                caches.open(STATIC_CACHE).then(cache => {
                                    cache.put(request, networkResponse);
                                });
                            }
                        })
                        .catch(() => {});
                    
                    return response;
                }
                
                return fetch(request)
                    .then(networkResponse => {
                        if (networkResponse && networkResponse.status === 200) {
                            const responseClone = networkResponse.clone();
                            caches.open(STATIC_CACHE).then(cache => { 
                                cache.put(request, responseClone);
                            });
                        }
                        return networkResponse;
                    })
                    .catch(() => {
                        return new Response('', { status: 404, statusText: 'Not Found' });
                    });
            })
    );
});

// Sincronização em segundo plano
self.addEventListener('sync', event => {
    if (event.tag === 'sync-alerts') {
        console.log('🔄 Sincronizando alertas pendentes...');
        event.waitUntil(syncAlerts());
    }
});

async function syncAlerts() {
    try {
        const clients = await self.clients.matchAll();
        clients.forEach(client => {
            client.postMessage({
                type: 'SYNC_ALERTS',
                timestamp: Date.now()
            });
        });
    } catch (error) {
        console.error('❌ Erro na sincronização:', error);
    }
}

// Mensagens do cliente
self.addEventListener('message', event => {
    console.log('📨 Mensagem recebida:', event.data);
    
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});