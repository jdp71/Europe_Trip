// Service worker disabled — unregister any old workers that may serve stale files.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.map((key) => caches.delete(key)))).then(() =>
      self.registration.unregister()
    )
  );
});
