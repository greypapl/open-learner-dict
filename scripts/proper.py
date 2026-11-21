"""专名层（proper-v1）：wordfreq zipf ≥ 3 中主词典和简释层都没收的词，写标准中文名；普通漏词顺手写简释。不经审核，confidence=low。

  python -X utf8 -I scripts/proper.py make [--size 500] [--min 3.0]   # → work/proper/P0001.in.txt …（按频率排序；再跑会追加新块，跳过已切过的词）
  python -X utf8 -I scripts/proper.py check [P0001 …]     # 校验 P*.out.txt
  python -X utf8 -I scripts/proper.py merge               # → work/merged/proper.jsonl（专名）+ proper-common.jsonl（普通漏词）+ proper-skips.jsonl

候选：zipf ≥ 3，排除已收（主词典、简释层，忽略大小写）、变形索引里的形式、含撇号或非字母的、单字母，
以及 skip 原因为 not-lemma / junk / not-english 的；主词典 skip 过的 proper-out-of-scope、abbr-rare 正是候选，保留。

prompt: prompts/proper.md
"""
import glob, json, re, sys
from pathlib import Path
from wordfreq import top_n_list, zipf_frequency

ROOT = Path(__file__).resolve().parent.parent
P, M = ROOT / 'work/proper', ROOT / 'work/merged'
sys.path.insert(0, str(ROOT / 'scripts'))
TYPES = {'place', 'person', 'brand', 'org', 'abbr', 'work', 'people', 'religion', 'event', 'other'}
SKIPS = {'junk', 'not-english', 'numeral', 'unknown', 'fragment'}
POS = r'(n\.|v\.|adj\.|adv\.|prep\.|conj\.|pron\.|det\.|int\.|num\.|abbr\.)'
SENSE = re.compile(r'^' + POS + r'(.+?)(?:\s*\[([^\]]+)\])?$')
TAGS = {'formal', 'informal', 'slang', 'dated', 'literary', 'uk', 'us', 'offensive-mild', 'offensive-strong'}
BAD = re.compile(r'[()（）；。;\[\]a-zA-Z]')


def zh_ok(z):
    return 1 <= len(z) <= 12 and not BAD.search(z)


def parse(line, word):
    f = [x.strip() for x in line.split(' | ')]
    if f[0] != word:
        raise ValueError(f'词头不符: {f[0]!r} ≠ {word!r}')
    if len(f) == 2 and f[1].startswith('skip:'):
        if f[1][5:] not in SKIPS:
            raise ValueError(f'skip 原因非法: {f[1]}')
        return {'skip': f[1][5:]}
    if len(f) >= 2 and f[1] == 'common':
        if len(f) not in (3, 4) or (len(f) == 4 and f[3] != 'nokid'):
            raise ValueError('common 行字段数不对')
        parts = [p.strip() for p in f[2].split(' ; ')]
        if len(parts) > 2:
            raise ValueError('超过 2 个义项')
        senses = []
        for p in parts:
            m = SENSE.match(p)
            if not m:
                raise ValueError(f'义项格式错: {p}')
            zh = [z.strip() for z in m.group(2).split(',') if z.strip()]
            if not 1 <= len(zh) <= 3 or not all(zh_ok(z) for z in zh):
                raise ValueError(f'中文不合规: {m.group(2)}')
            tags = [t.strip() for t in (m.group(3) or '').split(',') if t.strip()]
            for t in tags:
                if t not in TAGS and not t.startswith('domain:'):
                    raise ValueError(f'标签非法: {t}')
            senses.append({'pos': m.group(1), 'zh': zh, 'tags': tags})
        return {'common': senses, 'flags': ['nokid'] if len(f) == 4 else []}
    if len(f) != 3:
        raise ValueError('字段数不对')
    disp, names, also_common = f[1], [], False
    if disp.lower().replace(' ', '').replace('-', '').replace('.', '').replace('&', '') != word.replace('-', '').replace('.', ''):
        raise ValueError(f'Display 与词头不符: {disp}')
    rs = [r.strip() for r in f[2].split(' ; ')]
    for r in rs:
        if r == 'common':
            also_common = True
            continue
        m = re.match(r'^([a-z]+):([^=]+?)(?:=(.+))?$', r)
        if not m or m.group(1) not in TYPES:
            raise ValueError(f'读法格式错: {r}')
        if not zh_ok(m.group(2).strip()) or (m.group(3) and not zh_ok(m.group(3).strip())):
            raise ValueError(f'中文不合规: {r}')
        names.append({'type': m.group(1), 'zh': m.group(2).strip(), 'note': (m.group(3) or '').strip()})
    if not 1 <= len(names) <= 3:
        raise ValueError('读法数应为 1–3')
    return {'display': disp, 'names': names, 'also_common': also_common}


def chunk_names():
    return sorted(p.name[:5] for p in P.glob('P*.in.txt'))


def check(name):
    words = [l.strip() for l in open(P / f'{name}.in.txt', encoding='utf-8') if l.strip()]
    out = P / f'{name}.out.txt'
    if not out.exists():
        return None, ['missing']
    lines = [l.rstrip('\n') for l in open(out, encoding='utf-8') if l.strip()]
    errs, res = [], []
    if len(lines) != len(words):
        errs.append(f'行数 {len(lines)} ≠ 输入 {len(words)}')
    for i, (w, l) in enumerate(zip(words, lines), 1):
        try:
            res.append(parse(l, w))
        except ValueError as e:
            errs.append(f'第 {i} 行 {w}: {e}')
    return res, errs


def candidates(minz=3.0):
    have = set()
    for f in glob.glob(str(M / 'B[0-9][0-9][0-9][0-9].jsonl')):
        have |= {json.loads(l)['word'].lower() for l in open(f, encoding='utf-8')}
    have |= {json.loads(l)['word'].lower() for l in open(M / 'gloss.jsonl', encoding='utf-8')}
    skip = {}
    for f in glob.glob(str(M / 'B*.skips.jsonl')) + [str(M / 'gloss-skips.jsonl'), str(M / 'triage-skips.jsonl')]:
        for l in open(f, encoding='utf-8'):
            if l.strip():
                r = json.loads(l)
                skip[r['word'].lower()] = r['skip']
    inf = {json.loads(l)['form'].lower() for l in open(M / 'inflections.jsonl', encoding='utf-8')}
    inf |= {l.strip() for p in P.glob('P*.in.txt') for l in open(p, encoding='utf-8')}  # 已切块的词不再重复
    out = []
    for w in top_n_list('en', 400000):
        if zipf_frequency(w, 'en') < minz:
            break
        if (w in have or w in inf or len(w) < 2 or not re.fullmatch(r'[a-z][a-z.-]*[a-z]', w)
                or skip.get(w) in ('not-lemma', 'junk', 'not-english')):
            continue
        out.append(w)
    return out


cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
if cmd == 'make':
    size = int(sys.argv[sys.argv.index('--size') + 1]) if '--size' in sys.argv else 500
    P.mkdir(parents=True, exist_ok=True)
    minz = float(sys.argv[sys.argv.index('--min') + 1]) if '--min' in sys.argv else 3.0
    ws = candidates(minz)
    start = len(chunk_names())  # 追加切块，编号接在已有块后面
    for i in range(0, len(ws), size):
        (P / f'P{start + i // size + 1:04d}.in.txt').write_text('\n'.join(ws[i:i + size]) + '\n', encoding='utf-8')
    print(len(ws), 'candidates →', len(chunk_names()), 'chunks')
elif cmd == 'check':
    names = sys.argv[2:] or chunk_names()
    done = pn = cm = sk = 0
    pend = []
    for n in names:
        res, errs = check(n)
        if errs == ['missing']:
            pend.append(n); continue
        if errs:
            print(f'✗ {n}: {len(errs)} 处问题'); [print('  ', e) for e in errs[:15]]; continue
        done += 1
        a = sum('names' in r for r in res); b = sum('common' in r for r in res)
        pn += a; cm += b; sk += len(res) - a - b
        if len(sys.argv) > 2:
            print(f'✓ {n}: 专名 {a}，普通词 {b}，skip {len(res) - a - b}')
    print(f'通过 {done} 块：专名 {pn}，普通词 {cm}，skip {sk}；未完成 {len(pend)} 块 {" ".join(pend)}')
elif cmd == 'merge':
    np_ = nc = ns = 0
    with open(M / 'proper.jsonl', 'w', encoding='utf-8') as fp, open(M / 'proper-common.jsonl', 'w', encoding='utf-8') as fc, \
            open(M / 'proper-skips.jsonl', 'w', encoding='utf-8') as fs:
        for n in chunk_names():
            res, errs = check(n)
            if errs:
                sys.exit(f'{n} 未通过校验：{errs[0]}')
            words = [l.strip() for l in open(P / f'{n}.in.txt', encoding='utf-8') if l.strip()]
            for w, r in zip(words, res):
                z = round(zipf_frequency(w, 'en'), 2)
                base = {'word': w, 'zipf': z, 'confidence': 'low', 'source': 'proper-v1'}
                if 'names' in r:
                    fp.write(json.dumps(dict(base, display=r['display'], names=r['names'], also_common=r['also_common'],
                                             layer='proper'), ensure_ascii=False) + '\n'); np_ += 1
                elif 'common' in r:
                    fc.write(json.dumps(dict(base, senses=r['common'], flags=r['flags'], layer='gloss'),
                                        ensure_ascii=False) + '\n'); nc += 1
                else:
                    fs.write(json.dumps({'word': w, 'skip': r['skip'], 'by': 'proper-v1'}, ensure_ascii=False) + '\n'); ns += 1
    print(f'proper.jsonl {np_} 条，proper-common.jsonl {nc} 条，proper-skips.jsonl {ns} 个')
