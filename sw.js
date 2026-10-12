// 문득 — 오프라인 캐싱용 서비스워커
const CACHE_NAME = "moondeuk-v9";
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.json",
  "./foods.json",
  "./icon-192.png",
  "./icon-512.png"
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);

  // 같은 출처(우리 앱 파일)가 아니면 캐싱에 관여하지 않고 그대로 통과
  // (Firebase 인증·Firestore 통신이 서비스워커 캐싱에 걸려 깨지는 걸 방지)
  if (url.origin !== self.location.origin) {
    return;
  }

  e.respondWith(
    caches.match(e.request).then((cached) => {
      return (
        cached ||
        fetch(e.request)
          .then((res) => {
            const resClone = res.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(e.request, resClone));
            return res;
          })
          .catch(() => cached)
      );
    })
  );
});
