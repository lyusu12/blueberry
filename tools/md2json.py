# -*- coding: utf-8 -*-
# 쓰는 법: python3 tools/md2json.py olive.md  → 변환 결과(JSON)를 화면에 보여줌. 사전에 넣을 때는 build()를 불러 쓴다
# 초안(.md) → foods.json 항목(dict). 사용: build(path, checkedAt)
import re, json
EV = {'연구로 확인됨':'confirmed','근거가 약함':'weak','결과가 엇갈림':'mixed','밝혀진 바 없음':'unknown','사실과 다름':'false'}
BA = {'식품':'food','추출물':'extract'}
NUT = {'열량':'energy','탄수화물':'carbohydrate','당류':'sugars','식이섬유':'fiber','단백질':'protein','지방':'fat','포화지방':'saturatedFat','나트륨':'sodium'}
CATS = ['과일','채소','곡물','콩·견과','유제품·달걀','육류','생선·해산물','발효식품','기타']

def num(x):
    x = x.replace(',', '').strip()
    v = float(x)
    return int(v) if v.is_integer() and '.' not in x else v

def sections(text):
    out, cur = {}, None
    for line in text.split('\n'):
        m = re.match(r'^## (.+?)\s*(\(.*\))?\s*$', line)
        if m:
            cur = m.group(1).strip(); out[cur] = []; continue
        if cur is not None: out[cur].append(line)
    return out

def table(lines):
    rows = [l for l in lines if l.startswith('|')]
    body = []
    for r in rows[2:]:
        cells = [c.strip() for c in r.strip().strip('|').split('|')]
        body.append(cells)
    return body

def entries(lines):
    """**제목** (`id`) — 근거: X / 기준: Y / 참고자료 1, 2  +  > 설명"""
    out = []
    for l in lines:
        m = re.match(r'^\*\*(.+?)\*\*(.*)$', l)
        if m:
            title, meta = m.group(1).strip(), m.group(2)
            e = {'title': title, 'meta': meta, 'body': ''}
            t = re.search(r'\(`([a-z0-9-]+)`\)', meta)
            if t: e['target'] = t.group(1)
            ev = re.search(r'근거:\s*([^/]+?)\s*(/|$)', meta)
            if ev: e['evidence'] = EV[ev.group(1).strip()]
            ba = re.search(r'기준:\s*([^/]+?)\s*(/|$)', meta)
            if ba: e['basis'] = BA[ba.group(1).strip()]
            rf = re.search(r'참고자료\s*([\d,\s]+)', meta)
            if rf: e['refs'] = [int(x) for x in re.findall(r'\d+', rf.group(1))]
            out.append(e)
        elif l.startswith('> ') and out:
            out[-1]['body'] = (out[-1]['body'] + ' ' + l[2:].strip()).strip()
    return out

def clean(s):
    return re.sub(r'\*\*(.+?)\*\*', r'\1', s).strip()

def build(path, date):
    S = sections(open(path, encoding='utf-8').read())
    f = {}
    base = {}
    for l in S['기본']:
        m = re.match(r'^- \*\*(.+?)\*\*:\s*(.*)$', l)
        if m: base[m.group(1)] = m.group(2).strip()
    f['id'] = base['id'].split()[0]
    f['name'] = base['이름']
    if base.get('다른 이름') and base['다른 이름'] not in ('없음', '—'):
        f['aliases'] = [a.strip() for a in base['다른 이름'].split(',') if a.strip()]
    cat = base['분류'].split(' (')[0].strip()
    assert cat in CATS, cat
    f['categories'] = [cat]
    se = base.get('제철', '')
    if se and not se.startswith('없음'):
        m = re.match(r'(\d+)\s*~\s*(\d+)월', se)
        a, b = int(m.group(1)), int(m.group(2))
        months = list(range(a, b + 1)) if a <= b else list(range(a, 13)) + list(range(1, b + 1))
        note = re.search(r'\((.*)\)', se)
        f['season'] = {'months': months, 'note': note.group(1) if note else ''}
    f['summary'] = base['한 줄 소개']
    # 영양성분
    key = [k for k in S if k.startswith('영양성분')][0]
    nut = {}
    for name, val in [(r[0], r[1]) for r in table(S[key])]:
        if name in NUT:
            m = re.match(r'([\d.,]+)\s*(\S+)', val)
            nut[NUT[name]] = {'value': num(m.group(1)), 'unit': m.group(2)}
    f['nutrition'] = nut
    # 두드러지는 영양소
    hl = []
    for r in table(S['두드러지는 영양소']):
        h = {'nutrient': r[0]}
        m = re.match(r'([\d.,]+)\s*(\S+)', r[1])
        if m: h['amount'] = num(m.group(1)); h['unit'] = m.group(2)
        m = re.match(r'(\d+)%', r[2])
        if m: h['dv'] = int(m.group(1))
        h['role'] = clean(r[3])
        hl.append(h)
    f['highlights'] = hl
    f['choosing'] = [{'method': clean(r[0]), 'caution': clean(r[1])} for r in table(S['고르는법'])]
    st = []
    for r in table(S['보관 팁']):
        s = {'label': r[0], 'method': clean(r[1])}
        if r[2] and r[2] not in ('—', '-'): s['duration'] = clean(r[2])
        if r[3] and r[3] not in ('—', '-'): s['caution'] = clean(r[3])
        st.append(s)
    f['storage'] = st
    he = []
    for l in S['먹는 법']:
        m = re.match(r'^\d+\.\s*\*\*(.+?)\*\*\s*—\s*(.*)$', l)
        if m: he.append({'title': m.group(1).strip(), 'body': clean(m.group(2))})
    f['howToEat'] = he
    pa = []
    for e in entries(S.get('잘 어울리는 음식', [])):
        p = {}
        if 'target' in e: p['target'] = e['target']
        else: p['targetName'] = e['title']
        p['evidence'] = e['evidence']; p['basis'] = e.get('basis', 'food'); p['refs'] = e.get('refs', [])
        p['reason'] = clean(e['body'])
        pa.append(p)
    if pa: f['pairings'] = pa
    my = []
    for e in entries(S['속설']):
        my.append({'claim': e['title'], 'evidence': e['evidence'], 'basis': e.get('basis', 'food'),
                   'refs': e.get('refs', []), 'explanation': clean(e['body'])})
    f['myths'] = my
    refs = []
    for l in S['참고한 자료']:
        m = re.match(r'^(\d+)\.\s+(.*)\s+—\s+(https?://\S+)\s*$', l)
        if m: refs.append({'no': int(m.group(1)), 'source': m.group(2).strip(), 'url': m.group(3)})
    f['references'] = refs
    f['checkedAt'] = date
    return f

if __name__ == '__main__':
    import sys
    print(json.dumps(build(sys.argv[1], '2026-11-19'), ensure_ascii=False, indent=1))
