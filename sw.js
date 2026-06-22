/* Europe Trip offline cache — precache list built by app/build.py */
const PRECACHE_URL = "./precache.json";

self.addEventListener("install", (event) => {
  event.waitUntil(
    fetch(PRECACHE_URL)
      .then((res) => {
        if (!res.ok) throw new Error("precache.json missing");
        return res.json();
      })
      .then((manifest) => {
        self.__cacheVersion = manifest.version;
        const cacheName = `europe-trip-${manifest.version}`;
        return caches.open(cacheName).then((cache) =>
          Promise.allSettled(manifest.urls.map((url) => cache.add(url)))
        );
      })
      .then(() => self.skipWaiting())
      .catch((err) => {
        console.warn("SW install cache failed:", err);
        return self.skipWaiting();
      })
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    fetch(PRECACHE_URL)
      .then((res) => (res.ok ? res.json() : { version: "unknown" }))
      .then((manifest) => {
        self.__cacheVersion = manifest.version;
        const keep = `europe-trip-${manifest.version}`;
        return caches.keys().then((keys) =>
          Promise.all(keys.filter((k) => k.startsWith("europe-trip-") && k !== keep).map((k) => caches.delete(k)))
        );
      })
      .then(() => self.clients.claim())
  );
});

function cacheName() {
  return `europe-trip-${self.__cacheVersion || "fallback"}`;
}

function cacheFirst(request) {
  return caches.match(request).then((cached) => {
    if (cached) return cached;
    return fetch(request)
      .then((response) => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(cacheName()).then((cache) => cache.put(request, copy));
        }
        return response;
      })
      .catch(() => cached);
  });
}

function networkFirst(request) {
  return fetch(request)
    .then((response) => {
      if (response.ok) {
        const copy = response.clone();
        caches.open(cacheName()).then((cache) => cache.put(request, copy));
      }
      return response;
    })
    .catch(() => caches.match(request));
}

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  const respond = () => {
    if (event.request.mode === "navigate") {
      return caches.match("./index.html").then((cached) => cached || fetch(event.request));
    }
    if (url.pathname.endsWith("trip-data.json") || url.pathname.endsWith("precache.json")) {
      return networkFirst(event.request);
    }
    return cacheFirst(event.request);
  };

  if (self.__cacheVersion) {
    event.respondWith(respond());
    return;
  }

  event.respondWith(
    fetch(PRECACHE_URL)
      .then((res) => (res.ok ? res.json() : { version: "fallback" }))
      .then((manifest) => {
        self.__cacheVersion = manifest.version;
        return respond();
      })
      .catch(() => fetch(event.request))
  );
});
