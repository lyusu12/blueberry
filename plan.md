# 사전 데이터 구조 개편 계획

## 1. 파일 구성

| 파일 | 변경 |
|---|---|
| `foods.json` (새 파일) | 사전 데이터 전체. 항목을 늘릴 때는 이 파일만 고치면 돼요 |
| `index.html` | `NUTRI` 상수를 지우고, 시작할 때 `fetch("foods.json")`로 불러오기. 상세 화면 추가 |
| `sw.js` | `ASSETS`에 `foods.json` 추가, `CACHE_NAME`을 v7로 |
| `CLAUDE.md` | `foods.json` 형식 설명 추가 |

`foods.json`도 cache-first로 캐싱돼요. 그래서 **사전 항목만 고쳐도 `CACHE_NAME`을 올려야** 반영돼요. 지금 규칙("다른 파일을 고쳐도 올린다")으로 이미 커버되지만 CLAUDE.md에 한 번 더 명시할게요.

## 2. `foods.json` 구조

```json
{
  "dailyValues": {
    "energy": 2000, "carbohydrate": 324, "sugars": 100, "fiber": 25,
    "protein": 55, "fat": 54, "saturatedFat": 15, "sodium": 2000
  },
  "foods": [
    {
      "id": "blueberry",
      "name": "블루베리",
      "aliases": ["블루베리 생과"],
      "category": "과일",
      "season": { "months": [6, 7, 8], "note": "국내산 노지 기준" },
      "summary": "한 줄 소개",

      "nutrition": {
        "energy":       { "value": 57,   "unit": "kcal" },
        "carbohydrate": { "value": 14.5, "unit": "g" },
        "sugars":       { "value": 10,   "unit": "g" },
        "fiber":        { "value": 2.4,  "unit": "g" },
        "protein":      { "value": 0.7,  "unit": "g" },
        "fat":          { "value": 0.3,  "unit": "g" },
        "saturatedFat": { "value": 0,    "unit": "g" },
        "sodium":       { "value": 1,    "unit": "mg" }
      },

      "highlights": [
        { "nutrient": "비타민 K", "amount": 19.3, "unit": "µg", "dv": 27,
          "role": "혈액 응고와 뼈 건강에 관여해요" }
      ],

      "storage": [
        { "label": "고르기", "method": "…", "duration": "…", "caution": "…" },
        { "label": "냉장",   "method": "…", "duration": "3~5일", "caution": "…" }
      ],

      "howToEat": [
        { "title": "요거트 볼", "body": "그릭요거트에 올려…" }
      ],

      "pairings": [
        { "target": "oat", "reason": "…", "evidence": "confirmed", "refs": [1] }
      ],

      "myths": [
        { "claim": "…", "explanation": "…", "evidence": "false", "refs": [2] }
      ],

      "references": [
        { "no": 1, "source": "농촌진흥청 국가표준식품성분표 10.1", "url": "https://…" }
      ],

      "checkedAt": "2026-10-11"
    }
  ]
}
```

### 설계 포인트

- **`id`는 영문 슬러그**(`blueberry`)로 해요. 궁합 연결, 바구니 연결, 상세 화면 주소에 모두 이 값을 써요. 이름은 나중에 바뀔 수 있어서 이름을 키로 쓰지 않아요.
- **영양성분 %는 저장하지 않고 계산해요.** 기본 8개는 `value ÷ dailyValues`로 계산하고, 기준치는 식약처 1일 영양성분 기준치를 써요. 기준치가 바뀌면 숫자 하나만 고치면 되고, 값과 %가 서로 어긋날 일이 없어요.
  - 단, `highlights`의 비타민·미네랄은 종류가 너무 많아서 `dv`를 직접 적어요. 여기만 예외예요.
- **근거 등급은 영문 키 4개**로 저장하고, 화면에는 한글로 보여줘요.
  - `confirmed` 연구로 확인됨 / `mixed` 결과가 엇갈림 / `unknown` 밝혀진 바 없음 / `false` 사실과 다름
- **`refs`는 항목 안의 번호**예요. 각 식재료가 자기 `references`를 1번부터 따로 가져요.
- **궁합의 `target`은 다른 항목의 `id`**예요. 누르면 그 식재료 상세로 이동해요. 대상이 아직 사전에 없으면 링크 없이 텍스트로 보여주도록, 그런 경우를 위해 `"targetName": "오트밀"`을 선택 칸으로 둘게요.

### 빈 칸 처리 원칙

`id`와 `name`만 필수예요. 나머지는 다음처럼 처리해요.
- 섹션이 통째로 없거나 빈 배열이면 **제목까지 섹션을 숨겨요**.
- 숫자가 없으면 `—`으로 표시하고, 그 줄의 %도 계산하지 않아요.
- `storage`의 세 줄도 각각 없으면 그 줄만 생략해요.
- 근거 등급이 4개 중 하나가 아니면 배지를 숨겨요.

## 3. 화면: 식재료 상세 페이지 추가

궁합 링크로 이동하려면 상세 화면이 필요해요.

- `#view-food`를 새로 추가해요. 사전 목록에서 항목을 누르면 열려요.
- 주소는 **`#food/blueberry` 형태**로 하고, `hashchange`를 듣게 해요. 그러면 블루베리에서 오트밀로 갔다가 **뒤로가기로 블루베리에 돌아올 수 있어요.** 지금의 탭 전환 방식은 그대로 두고 상세 화면에만 hash를 써요.
- 사전 목록은 이름, 분류, 한 줄 소개, 「담기」 버튼으로 단순하게 바꿔요.
- 상세 화면도 「담기」 버튼을 가져요.
- 텍스트가 많아지므로 **렌더링은 `innerHTML` 대신 `textContent` 기반**으로 바꿔요. 이전에 말씀드린 XSS 문제도 같이 해결돼요.

## 4. 기존 `items`와의 연결

```js
{ id, name, cat, memo, lastEaten,
  foodId: "blueberry",     // 새로 추가 (선택). 사전 항목과 연결
  nutri: {kcal,key,note}   // 기존 필드 유지. 사전과 연결 안 된 직접 입력 항목용
}
```

- **사전에서 담으면** `foodId`만 저장하고 영양 정보는 복사하지 않아요. 화면에 그릴 때 사전에서 찾아와요. 사전을 고치면 바구니에도 바로 반영돼요.
- **직접 입력한 항목**은 지금처럼 `nutri`를 그대로 써요.
- **「담음」 여부**는 이름 비교 대신 `foodId`로 판단해요.
- **뽑기 카드와 바구니 목록**은 이렇게 보여줘요.
  - `foodId`가 있으면: 열량, 한 줄 소개, 「자세히 보기」 링크
  - 없으면: 기존 `nutri` 표시 그대로
  - 뽑기 가중치와 필터는 손대지 않아요.
- **기존 데이터 이전**: 처음 불러올 때, `foodId`가 없는 항목의 이름이 사전의 `name`이나 `aliases`와 정확히 같으면 `foodId`를 붙여요.
  - 이전은 한 번만 실행되고, 바뀐 내용은 Firestore에도 올라가요.
  - `nutri`는 지우지 않고 남겨요. 그래서 예전 버전 앱이 켜진 다른 기기에서도 깨지지 않아요.
  - `연어 스테이크`처럼 이름이 다른 항목은 연결되지 않고 지금처럼 동작해요.
- **로딩 순서**: 바구니와 뽑기는 `localStorage`로 바로 그리고, 사전은 `foods.json`이 도착한 뒤에 그려요. 불러오기에 실패해도 바구니와 뽑기는 정상 동작해요.

## 5. 기존 `NUTRI` 30개 옮기기

기존 30개는 아래처럼 들어 있는 정보만 옮겨요.
- `kcal` → `nutrition.energy`
- `note` → `summary`
- `key` → `highlights[0].nutrient`
- 분류는 제가 채울게요 (예: 연어 → 수산물).

나머지 칸은 비워 두고 `checkedAt`도 비워서 "아직 검증 안 된 항목"으로 구분해요. 제가 영양성분 수치를 추측해서 채우지는 않을게요.

## 확인해 주실 것

1. 파일 이름은 `foods.json`(루트), 상세 주소는 `#food/{id}` 형식으로 괜찮을까요?
2. 분류 목록을 정해 둘까요? 제안은 **과일 / 채소 / 곡물 / 콩·견과 / 유제품·달걀 / 육류 / 수산물 / 발효식품 / 기타**예요. 김치, 낫토, 다크초콜릿처럼 애매한 것들이 있어서요.
3. 사전에서 담을 때 바구니 카테고리는 지금처럼 항상 `식재료`로 넣으면 될까요?
