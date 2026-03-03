self.addEventListener("install", event => {
  console.log("Service Worker instalado");
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  console.log("Service Worker ativado");
  return self.clients.claim();
});

self.addEventListener("push", function(event) {
  if (!event.data) {
    return;
  }

  const data = event.data.json();

  const options = {
    body: data.body || "Alerta recebido",
    icon: "/static/icon-192.png",
    badge: "/static/icon-192.png",
    vibrate: [200, 100, 200],
    data: {
      url: data.url || "/trusted/panel"
    }
  };

  event.waitUntil(
    self.registration.showNotification(data.title || "Aurora", options)
  );
});

self.addEventListener("notificationclick", function(event) {
  event.notification.close();

  const url = event.notification.data.url;

  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then(function(clientList) {
      for (let i = 0; i < clientList.length; i++) {
        const client = clientList[i];
        if (client.url.includes(url) && "focus" in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(url);
      }
    })
  );
});