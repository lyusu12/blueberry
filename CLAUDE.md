# 문득

빌드 없는 단일 파일 PWA (`index.html`, `foods.json`, `manifest.json`, `sw.js`, 아이콘).

## 규칙

- **코드를 수정하면 `sw.js`의 `CACHE_NAME` 버전을 반드시 함께 올릴 것.**
  (예: `meokkitlist-v6` → `meokkitlist-v7`)
  서비스워커가 cache-first라서, 버전을 올리지 않으면 설치된 앱에 수정 사항이 반영되지 않는다.
  **`foods.json`(사전 데이터)만 고친 경우에도 마찬가지로 올린다.**

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
  "storage":    [{ "label": "냉장", "method": "방법", "duration": "기간", "caution": "주의사항" }],
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
- 분류 목록: 과일 / 채소 / 곡물 / 콩·견과 / 유제품·달걀 / 육류 / 수산물 / 발효식품 / 기타

## 바구니 항목 (`items`, localStorage + Firestore)

`{ id, name, cat, memo, lastEaten, foodId?, nutri? }`
- `foodId`가 있으면 사전에서 정보를 읽어서 보여준다 (복사하지 않음).
- `nutri`({kcal,key,note})는 사전과 연결 안 된 직접 입력 항목용. 예전 버전 앱 호환을 위해 지우지 않는다.
