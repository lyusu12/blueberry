// 블루베리 — 오프라인 캐싱용 서비스워커
const CACHE_NAME = "blueberry-v16";
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
    // cache: "reload" — 브라우저가 들고 있던 옛 파일 말고 항상 서버에서 새로 받아 담음
    // (안 그러면 버전을 올려도 GitHub Pages의 10분 캐시 때문에 옛 foods.json이 들어갈 수 있음)
    caches.open(CACHE_NAME).then((cache) =>
      cache.addAll(ASSETS.map((url) => new Request(url, { cache: "reload" })))
    )
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
