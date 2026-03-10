// Service Worker para Aurora - Modo offline básico
const CACHE_NAME = 'aurora-cache-v1';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/icons/favicon-32.png',
  '/static/icons/apple-touch-icon.png'
];

// Instalação do Service Worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('✅ Cache aberto');
        return cache.addAll(urlsToCache);
      })
  );
});

// Ativação e limpeza de caches antigos
self.addEventListener('activate', event => {
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
    })
  );
});

// Interceptar requisições
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Retorna do cache se encontrou
        if (response) {
          return response;
        }
        
        // Se não encontrou, busca na rede
        return fetch(event.request).then(
          networkResponse => {
            // Verifica se é uma resposta válida
            if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
              return networkResponse;
            }

            // Clona e salva no cache
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });

            return networkResponse;
          }
        );
      })
      .catch(() => {
        // Fallback offline
        if (event.request.url.includes('.html')) {
          return caches.match('/');
        }
      })
  );
});