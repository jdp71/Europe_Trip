const CACHE = "europe-trip-v9";

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then(async (cache) => {
      const res = await fetch("./trip-data.json");
      const data = await res.json();
      const urls = [
        "./",
        "./index.html",
        "./manifest.json",
        "./trip-data.json",
        "./css/app.css",
        "./js/app.js",
        "./vendor/pdf.min.js",
        "./vendor/pdf.worker.min.js",
        "./icons/icon-192.png",
        "./icons/icon-512.png",
      ];
      for (const pdf of data.pdfs || []) {
        urls.push(`./documents/${pdf}`);
      }
      for (const asset of data.assets || []) {
        urls.push(`./${asset}`);
      }
      await cache.addAll(urls.filter(Boolean));
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(
    caches.match(event.request).then((cached) => {
      const fetched = fetch(event.request)
        .then((res) => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(CACHE).then((c) => c.put(event.request, clone));
          }
          return res;
        })
        .catch(() => cached);
      return cached || fetched;
    })
  );
});
