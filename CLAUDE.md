# 문득

빌드 없는 단일 파일 PWA (`index.html`, `manifest.json`, `sw.js`, 아이콘).

## 규칙

- **코드를 수정하면 `sw.js`의 `CACHE_NAME` 버전을 반드시 함께 올릴 것.**
  (예: `meokkitlist-v6` → `meokkitlist-v7`)
  서비스워커가 cache-first라서, 버전을 올리지 않으면 설치된 앱에 수정 사항이 반영되지 않는다.
