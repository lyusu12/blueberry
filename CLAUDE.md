# 문득

빌드 없는 단일 파일 PWA (`index.html`, `foods.json`, `manifest.json`, `sw.js`, 아이콘).

## 규칙

- **코드를 수정하면 `sw.js`의 `CACHE_NAME` 버전을 반드시 함께 올릴 것.**
  (예: `moondeuk-v1` → `moondeuk-v2`)
  서비스워커가 cache-first라서, 버전을 올리지 않으면 설치된 앱에 수정 사항이 반영되지 않는다.
  **`foods.json`(사전 데이터)만 고친 경우에도 마찬가지로 올린다.**
- **localStorage 키 `meokkit_items_v2`와 Firestore 컬렉션 `meokkit_users`는 이름을 바꾸지 않는다.**
  예전 앱 이름(먹킷리스트)의 흔적이지만, 바꾸면 기존 사용자 데이터를 못 읽는다.
  Firebase 설정의 `meokkit-12b18`도 실제 프로젝트 ID라 바꾸지 않는다.

## 사전 데이터 (`foods.json`)

사전 항목은 코드가 아니라 `foods.json`에 있다. 항목 추가·수정은 이 파일만 고친다.

- 필수는 `id`, `name`뿐. 나머지 칸은 비우거나 빼도 화면이 깨지지 않는다 (빈 섹션은 숨김).
- `id`는 영문 슬러그(`blueberry`). 궁합 연결, 바구니 연결(`items[].foodId`), 상세 주소(`#food/{id}`)에 쓰이므로 **한번 정하면 바꾸지 않는다.**
- 영양성분 %는 저장하지 않는다. 최상위 `dailyValues`(식약처 1일 영양성분 기준치)로 계산한다.
  단위는 `energy`=kcal, `sodium`=mg, 나머지 g. 단위가 다르면 %를 표시하지 않는다.
- `highlights[].dv`(기준치 대비 %)만 직접 적는다.

```jsonc
{
  "id": "blueberry",
  "name": "블루베리",
  "aliases": ["블루베리 생과"],          // 바구니 항목 이름이 이 중 하나와 같으면 자동 연결
  "categories": ["과일"],                // 여러 개 가능
  "season": { "months": [6, 7, 8], "note": "국내산 노지 기준" },
  "summary": "한 줄 소개",
  "nutrition": {                         // 100g 기준. 8개 키 중 있는 것만
    "energy": { "value": 57, "unit": "kcal" },
    "carbohydrate": {...}, "sugars": {...}, "fiber": {...},
    "protein": {...}, "fat": {...}, "saturatedFat": {...}, "sodium": { "value": 1, "unit": "mg" }
  },
  "highlights": [{ "nutrient": "비타민 K", "amount": 19.3, "unit": "µg", "dv": 27, "role": "하는 일" }],
  "image":      { "src": "images/blueberry.jpg", "alt": "설명" },   // 없으면 분류 색 배경만 표시
  "choosing":   [{ "method": "고르는 방법", "caution": "주의사항" }],              // 「고르는법」 섹션 (label은 선택)
  "storage":    [{ "label": "냉장", "method": "방법", "duration": "기간", "caution": "주의사항" }],  // 「보관 팁」 섹션. 상온·냉장·냉동 등 여러 개
  "howToEat":   [{ "title": "요거트 볼", "body": "간단한 조리법" }],
  "pairings":   [{ "target": "oat", "targetName": "오트밀", "reason": "왜 좋은지",
                   "evidence": "confirmed", "basis": "food", "refs": [1] }],
  "myths":      [{ "claim": "주장", "explanation": "설명",
                   "evidence": "false", "basis": "extract", "refs": [2] }],
  "references": [{ "no": 1, "source": "출처 설명", "url": "https://…" }],
  "checkedAt": "2026-10-11"              // null이면 "아직 검증되지 않은 항목"으로 표시
}
```

- `evidence`(근거 등급): `confirmed` 연구로 확인됨 / `mixed` 결과가 엇갈림 / `unknown` 밝혀진 바 없음 / `false` 사실과 다름
- `basis`(연구 기준): `food` 식품 기준 / `extract` 추출물 기준. `extract`면 "음식으로 먹는 양에서는 효과가 작을 수 있다"는 안내가 붙는다.
- `pairings[].target`은 다른 항목의 `id`. 사전에 아직 없는 식재료면 `targetName`을 텍스트로 보여준다.
- `refs`는 같은 항목의 `references[].no`를 가리킨다 (항목마다 1번부터).
- 분류 목록: 과일 / 채소 / 곡물 / 콩·견과 / 유제품·달걀 / 육류 / 생선·해산물 / 발효식품 / 기타
  (첫 번째 분류가 사진이 없을 때의 배경색을 정한다. 색은 `index.html`의 `CATEGORY_TINT`)
- `image.src`는 상대 경로(예: `images/blueberry.jpg`) 또는 https 주소. 사진을 못 불러오면 색 배경으로 돌아간다.
- 영양성분·두드러지는 영양소를 뺀 섹션은 접히는 카드(`foldSection`): 처음엔 요약만, 누르면 자세히. 참고한 자료는 요약 없이 제목만
- 상세 화면 섹션 순서와 이름은 고정: 영양성분 / 두드러지는 영양소 / 고르는법 / 보관 팁 / 먹는 법 / 잘 어울리는 음식 / 속설 / 참고한 자료

## 바구니 항목 (`items`, localStorage + Firestore)

`{ id, name, cat, memo, lastEaten, foodId?, nutri? }`
- `foodId`가 있으면 사전에서 정보를 읽어서 보여준다 (복사하지 않음).
- `nutri`({kcal,key,note})는 사전과 연결 안 된 직접 입력 항목용. 예전 버전 앱 호환을 위해 지우지 않는다.

## 메뉴 구조

- 하단 탭: 홈 · 사전 · 바구니 · 설정(view-settings, 계정 포함). 「오늘 뭐 먹지?」(view-pick, 예전 뽑기)는 사이드 메뉴에서만 들어감
- 사이드 메뉴 항목은 `MENU` 배열에서만 정의 (`id`, `label`, `icon`, `go:{tab, filter}`, `children`). 데이터·화면이 없는 메뉴는 넣지 않는다
- 사전 필터 `dictFilter`: `{type:"all"}` / `{type:"cat", cat}` / `{type:"season", month}` / `{type:"viewed"}`(인기 = 이 기기에서 많이 본 순)
- 완성 음식은 사전 항목에 `"kind": "dish"`, `"cuisine": "한식"|"양식"|"중식"|"일식"|"간식·디저트"` (잠정). 「음식·레시피」(view-dishes)에 보이고 식재료 목록에선 빠짐

## 홈 화면

- 「오늘의 발견」: 날짜로 정해지는 **검증 완료(`checkedAt`) 항목** 최대 3개 (하루 동안 같음)
- 「요즘 제철」: `season.months`에 이번 달이 들어 있는 항목만. 없으면 안내 문구
- 「자주 본 식재료」: 상세 화면을 연 횟수(이 기기의 localStorage `moondeuk_views`) 순. 기록이 없으면 「사전 둘러보기」로 사전 앞쪽 5개
- 디자인 색·간격은 `index.html` 맨 위 `:root` 변수에 모여 있음 (딥퍼플 `--primary` #514568, 크림 `--bg` #FAF8F4)
