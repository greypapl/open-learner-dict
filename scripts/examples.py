"""例句层（example-v1）：主词典常用词每个义项 1 句英文例句 + 简体译文（繁体由 release.py 转）。

  python -X utf8 -I scripts/examples.py make [--top 5000] [--max-level C1] [--size 300]   # release/<ver>/jsonl/core.jsonl rank ≤ top → work/examples/E0001.in.txt
  python -X utf8 -I scripts/examples.py check [E0001 …]                 # 校验 E*.out.txt
  python -X utf8 -I scripts/examples.py review-make [--size 2000]       # 写手结果 → 审核块 work/examples/V0001.in.txt
  python -X utf8 -I scripts/examples.py review-check [V0001 …]          # 校验 V*.reviewer.txt（只含要改的行）
  python -X utf8 -I scripts/examples.py apply                           # 写手 + 审核 → work/merged/examples.jsonl

输入行：sense_id | word | pos | level | 中文释义 | en_short
写手输出：sense_id | 英文例句 | 中文译文        审核输出（只写要改的）：sense_id | 改后英文 | 改后中文
prompts: prompts/example-writer.md, prompts/example-reviewer.md
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D, M = ROOT / 'work/examples', ROOT / 'work/merged'
VER = sys.argv[sys.argv.index('--version') + 1] if '--version' in sys.argv else '0.10.0'
REL = ROOT / 'release' / VER / 'jsonl'
CJK = re.compile(r'[㐀-鿿]')


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def names(prefix):
    sel = [a for a in sys.argv[2:] if re.fullmatch(prefix + r'\d{4}', a)]
    return sel or sorted(p.name[:5] for p in D.glob(f'{prefix}*.in.txt'))


def inputs(name):
    src = {}
    for l in open(D / f'{name}.in.txt', encoding='utf-8'):
        f = l.rstrip('\n').split(' | ')
        src[f[0]] = f
    return src


_forms = None


def forms(word):
    global _forms
    if _forms is None:
        _forms = {}
        for l in open(M / 'inflections.jsonl', encoding='utf-8'):
            r = json.loads(l)
            for x in r['lemmas']:
                _forms.setdefault(x['lemma'].lower(), set()).add(r['form'].lower())
    w = word.lower()
    return _forms.get(w, set()) | {w}


def has_word(word, en):
    toks = re.findall(r"[a-z]+(?:[-'][a-z]+)*", en.lower().replace('’', "'"))
    fs = forms(word)
    if any(t in fs or t.split("'")[0] in fs for t in toks):
        return True
    w = word.lower()
    if '-' in w or ' ' in w or "'" in w:
        return w in en.lower()
    stem = w[:max(3, len(w) - 2)]  # 不规则变形没收录时的宽松兜底：前缀相同
    return any(t.startswith(stem) for t in toks)


def parse(line, src):
    f = [x.strip() for x in line.split(' | ')]
    if len(f) != 3:
        raise ValueError(f'字段数 {len(f)} ≠ 3')
    sid, en, zh = f
    if sid not in src:
        raise ValueError(f'sense_id 不在输入中: {sid}')
    n = len(en.split())
    if not 4 <= n <= 22:
        raise ValueError(f'英文 {n} 个词（要 4–22）')
    if not re.match(r'^["“‘(]?[A-Z0-9]', en) or not re.search(r'[.!?]["”’)]?$', en):
        raise ValueError('英文要大写开头、句末标点结尾')
    if CJK.search(en):
        raise ValueError('英文里有汉字')
    if not has_word(src[sid][1], en):
        raise ValueError(f'例句里找不到词头 {src[sid][1]} 或其变形')
    if not CJK.search(zh) or len(zh) > 60:
        raise ValueError('中文译文为空或过长')
    return sid, en, zh


def read(name, suffix):
    src, res, errs = inputs(name), {}, []
    o = D / f'{name}.{suffix}.txt'
    if not o.exists():
        return src, None, []
    for i, l in enumerate(open(o, encoding='utf-8'), 1):
        if not l.strip():
            continue
        try:
            sid, en, zh = parse(l, src)
            if sid in res:
                raise ValueError(f'重复: {sid}')
            res[sid] = (en, zh)
        except ValueError as e:
            errs.append(f'{o.name} 第 {i} 行 {e}：{l.strip()[:70]}')
    return src, res, errs


cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
if cmd == 'make':
    D.mkdir(parents=True, exist_ok=True)
    top, size = arg('--top', 5000), arg('--size', 300)
    maxlv = arg('--max-level', '')  # 例如 C1：不论名次，A1–C1 的词都选（'A1' < … < 'C2' 按字符串比较正好有序）
    rows = sorted((json.loads(l) for l in open(REL / 'core.jsonl', encoding='utf-8')), key=lambda r: r['rank'])
    L = [f"{s['sense_id']} | {r['word']} | {s['pos']} | {r['level'] or '-'} | {s['zh']} | {s['en_short']}"
         for r in rows if r['rank'] <= top or r['level'] <= maxlv for s in r['senses']]
    # 增量：已经切过块的 sense_id 不再切；新块接着编号（排名变了也不影响旧块）
    done = set()
    for p in D.glob('E*.in.txt'):
        done |= set(inputs(p.name[:5]))
    L = [l for l in L if l.split(' | ')[0] not in done]
    if not L:
        sys.exit('没有新的义项')
    start = len(list(D.glob('E*.in.txt')))
    chunks, cur = [], []  # 不拆开同一个词的义项：块边界顺延到下一个词开头
    for l in L:
        if len(cur) >= size and l.split(' | ')[0].split('.')[0] != cur[-1].split(' | ')[0].split('.')[0]:
            chunks.append(cur); cur = []
        cur.append(l)
    chunks.append(cur)
    for j, c in enumerate(chunks, start + 1):
        (D / f'E{j:04d}.in.txt').write_text('\n'.join(c) + '\n', encoding='utf-8')
    print(f'新义项 {len(L)} 个 → {len(chunks)} 块 E{start + 1:04d}–E{start + len(chunks):04d}')
elif cmd == 'check':
    tot = 0
    for n in names('E'):
        src, res, errs = read(n, 'out')
        if res is None:
            print(f'{n}: 未完成'); continue
        miss = [s for s in src if s not in res]
        for e in errs[:20]:
            print('✗', e)
        if miss:
            print(f'✗ {n} 缺 {len(miss)} 个义项：{" ".join(miss[:10])}')
        print(f'{n}: {len(res)}/{len(src)} 条，错误 {len(errs)}，缺 {len(miss)}')
        tot += len(res)
    print('合计', tot)
elif cmd == 'review-make':
    size = arg('--size', 2000)
    done = set()  # 增量：已经进过审核块的不再进；新块接着编号
    for p in D.glob('V*.in.txt'):
        done |= {l.split(' | ')[0] for l in open(p, encoding='utf-8')}
    L = []
    for n in names('E'):
        src, res, errs = read(n, 'out')
        if res is None or errs or len(res) != len(src):
            sys.exit(f'{n} 还没通过 check')
        for sid, f in src.items():
            if sid not in done:
                L.append(f'{sid} | {f[1]} | {f[2]} | {f[4]} | {f[5]} | {res[sid][0]} | {res[sid][1]}')
    if not L:
        sys.exit('没有新的审核条目')
    start = len(list(D.glob('V*.in.txt')))
    for i in range(0, len(L), size):
        (D / f'V{start + i // size + 1:04d}.in.txt').write_text('\n'.join(L[i:i + size]) + '\n', encoding='utf-8')
    print(f'新条目 {len(L)} 条 → {(len(L) - 1) // size + 1} 块审核，从 V{start + 1:04d} 起')
elif cmd in ('review-check', 'apply'):
    allsrc = {}
    for n in names('E'):
        allsrc.update(inputs(n))
    fixes, bad = {}, 0
    for n in names('V'):
        o = D / f'{n}.reviewer.txt'
        if not o.exists():
            print(f'{n}: 未完成'); bad += 1; continue
        vs = {l.split(' | ')[0]: l for l in open(D / f'{n}.in.txt', encoding='utf-8')}
        k = 0
        for i, l in enumerate(open(o, encoding='utf-8'), 1):
            if not l.strip():
                continue
            f = [x.strip() for x in l.split(' | ')]
            if len(f) == 7:
                f = [f[0], f[5], f[6]]  # 整行抄回来的：取最后两栏
                l = ' | '.join(f)
            try:
                if f[0] not in vs:
                    raise ValueError('sense_id 不在审核块里')
                sid, en, zh = parse(l, allsrc)
                fixes[sid] = (en, zh); k += 1
            except (ValueError, IndexError) as e:
                bad += 1
                print(f'✗ {o.name} 第 {i} 行 {e}：{l.strip()[:70]}')
        print(f'{n}: 改 {k} 条')
    if cmd == 'apply':
        if bad:
            sys.exit('审核还有问题，先修')
        out = []
        for n in names('E'):
            src, res, errs = read(n, 'out')
            for sid in src:
                en, zh = fixes.get(sid, res[sid])
                out.append({'sense_id': sid, 'en': en, 'zh': zh, 'reviewed': True, 'revised': sid in fixes})
        with open(M / 'examples.jsonl', 'w', encoding='utf-8', newline='\n') as f:
            for r in out:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        print(f'work/merged/examples.jsonl {len(out)} 条（审核改了 {len(fixes)} 条）')
