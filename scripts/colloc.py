"""搭配层（colloc-v1）：常用实词的强搭配（make a decision、heavy rain、highly likely）。

  python -X utf8 -I scripts/colloc.py make [--top 5000] [--size 100]   # 主词典按 zipf 取前 N 个有 n./v./adj./adv. 义项的词头 → work/colloc/K0001.in.txt
  python -X utf8 -I scripts/colloc.py check [K0001 …]                 # 校验 K*.out.txt
  python -X utf8 -I scripts/colloc.py merge                           # → work/merged/collocations.jsonl（按搭配去重，headword 可多个）
  python -X utf8 -I scripts/colloc.py review-make [--size 400]        # collocations.jsonl → 审核块 work/colloc/J0001.in.txt
  python -X utf8 -I scripts/colloc.py review-check [J0001 …]          # 校验 J*.reviewer.txt（改正行或 delete 行）
  python -X utf8 -I scripts/colloc.py review-apply                    # 应用审核 → collocations.jsonl（review_status）+ colloc-deletes.jsonl
  审核 prompt: prompts/colloc-reviewer.md

prompt: prompts/colloc.md
"""
import glob, json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D, M = ROOT / 'work/colloc', ROOT / 'work/merged'
PATTERNS = {'v+n', 'adj+n', 'n+n', 'adv+adj', 'v+adv', 'v+prep'}
BAD = re.compile(r'[()（）；。;\[\]a-zA-Z]')


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def parse(line, heads):
    f = [x.strip() for x in line.split(' | ')]
    if len(f) != 4:
        raise ValueError(f'字段数 {len(f)} ≠ 4')
    col, pat, zh, hw = f
    if ' ' not in col or not re.fullmatch(r"[a-z][a-z' .-]*[a-z.]", col):
        raise ValueError(f'搭配不合规: {col}')
    if pat not in PATTERNS:
        raise ValueError(f'模式非法: {pat}')
    zs = [z.strip() for z in zh.split(',') if z.strip()]
    if not 1 <= len(zs) <= 2 or any(len(z) > 12 or BAD.search(z) for z in zs):
        raise ValueError(f'中文不合规: {zh}')
    if hw not in heads:
        raise ValueError(f'headword 不在输入中: {hw}')
    return {'collocation': col, 'pattern': pat, 'zh': zs, 'headword': hw}


def check(name):
    heads = {l.strip() for l in open(D / f'{name}.in.txt', encoding='utf-8') if l.strip()}
    out = D / f'{name}.out.txt'
    if not out.exists():
        return None, ['missing']
    res, errs = [], []
    for i, l in enumerate(open(out, encoding='utf-8'), 1):
        if l.strip():
            try:
                res.append(parse(l.rstrip('\n'), heads))
            except ValueError as e:
                errs.append(f'第 {i} 行: {e} :: {l.strip()[:70]}')
    return res, errs


def names():
    return sorted(p.name[:5] for p in D.glob('K*.in.txt'))


DEL = re.compile(r'^(.+?) \| delete:(free|wrong|phrase|rare)$')


def read_review(name):
    src = {}
    for l in open(D / f'{name}.in.txt', encoding='utf-8'):
        if l.strip():
            src[l.split(' | ')[0].strip()] = l.rstrip('\n')
    out, errs = {}, []
    p = D / f'{name}.reviewer.txt'
    if not p.exists():
        return None, src, ['missing']
    for i, l in enumerate(open(p, encoding='utf-8'), 1):
        l = l.strip()
        if not l:
            continue
        m = DEL.match(l)
        key = m.group(1).strip() if m else l.split(' | ')[0].strip()
        if key not in src:
            errs.append(f'第 {i} 行不在输入中: {key}'); continue
        if m:
            out[key] = {'delete': m.group(2)}; continue
        try:
            heads = set(src[key].split(' | ')[3].split(','))
            f = [x.strip() for x in l.split(' | ')]
            r = parse(' | '.join(f[:3] + [f[3].split(',')[0]]), heads) if len(f) == 4 else parse(l, heads)
            out[key] = r
        except ValueError as e:
            errs.append(f'第 {i} 行: {e}')
    return out, src, errs


cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
if cmd == 'make':
    top, size = arg('--top', 5000), arg('--size', 100)
    rows = []
    for f in glob.glob(str(M / 'B[0-9][0-9][0-9][0-9].jsonl')):
        for l in open(f, encoding='utf-8'):
            r = json.loads(l)
            if r['word'].isalpha() and r['word'].islower() and any(s['pos'] in ('n.', 'v.', 'adj.', 'adv.') for s in r['senses']):
                rows.append((r.get('zipf') or 0, r['word']))
    words = [w for _, w in sorted(rows, reverse=True)][:top]
    D.mkdir(parents=True, exist_ok=True)
    for i in range(0, len(words), size):
        (D / f'K{i // size + 1:04d}.in.txt').write_text('\n'.join(words[i:i + size]) + '\n', encoding='utf-8')
    print(len(words), 'headwords →', (len(words) - 1) // size + 1, 'chunks')
elif cmd == 'check':
    tot, pend = 0, []
    for n in [a for a in sys.argv[2:] if re.fullmatch(r'K\d{4}', a)] or names():
        res, errs = check(n)
        if errs == ['missing']:
            pend.append(n); continue
        if errs:
            print(f'✗ {n}: {len(errs)} 处问题'); [print('  ', e) for e in errs[:20]]; continue
        tot += len(res)
        print(f'✓ {n}: {len(res)} 条（{dict(Counter(r["pattern"] for r in res))}）')
    print(f'合计 {tot} 条；未完成 {len(pend)} 块')
elif cmd == 'merge':
    by = {}
    phr = {json.loads(l)['phrase'].lower() for l in open(M / 'phrases.jsonl', encoding='utf-8')}  # 已在短语层的不重复收
    dup = cut = 0
    per = Counter()  # 每个词头最多 8 条（按写手给出的顺序，先写的优先）
    for n in names():
        res, errs = check(n)
        if errs:
            sys.exit(f'{n} 未通过：{errs[0]}')
        for r in res:
            if r['collocation'] in phr:
                dup += 1; continue
            if r['collocation'] not in by and per[r['headword']] >= 8:
                cut += 1; continue
            per[r['headword']] += r['collocation'] not in by
            e = by.setdefault(r['collocation'], dict(r, headword=[], layer='collocation', confidence='low', source='colloc-v1'))
            if r['headword'] not in e['headword']:
                e['headword'].append(r['headword'])
    with open(M / 'collocations.jsonl', 'w', encoding='utf-8') as f:
        for e in by.values():
            f.write(json.dumps(e, ensure_ascii=False) + '\n')
    print(f'collocations.jsonl {len(by)} 条（与短语层重复去掉 {dup}，超过每词 8 条上限去掉 {cut}）')
elif cmd == 'review-make':
    rows = [json.loads(l) for l in open(M / 'collocations.jsonl', encoding='utf-8')]
    lines = [f"{r['collocation']} | {r['pattern']} | {', '.join(r['zh'])} | {','.join(r['headword'])}" for r in rows]
    size = arg('--size', 400)
    for old in D.glob('J*.in.txt'):
        old.unlink()
    for i in range(0, len(lines), size):
        (D / f'J{i // size + 1:04d}.in.txt').write_text('\n'.join(lines[i:i + size]) + '\n', encoding='utf-8')
    print(len(lines), 'collocations →', (len(lines) - 1) // size + 1, 'review chunks')
elif cmd == 'review-check':
    pend = []
    for n in [a for a in sys.argv[2:] if re.fullmatch(r'J\d{4}', a)] or sorted(p.name[:5] for p in D.glob('J*.in.txt')):
        out, src, errs = read_review(n)
        if errs == ['missing']:
            pend.append(n); continue
        if errs:
            print(f'✗ {n}: {len(errs)} 处问题'); [print('  ', e) for e in errs[:20]]; continue
        d = sum('delete' in r for r in out.values())
        print(f'✓ {n}: 改 {len(out) - d}，删 {d}（{dict(Counter(r["delete"] for r in out.values() if "delete" in r))}）')
    print(f'未完成 {len(pend)} 块 {" ".join(pend)}')
elif cmd == 'review-apply':
    rows = {json.loads(l)['collocation']: json.loads(l) for l in open(M / 'collocations.jsonl', encoding='utf-8')}
    fixed = deleted = 0
    with open(M / 'colloc-deletes.jsonl', 'w', encoding='utf-8') as fd:
        for n in sorted(p.name[:5] for p in D.glob('J*.in.txt')):
            out, src, errs = read_review(n)
            if errs:
                sys.exit(f'{n} 审核未完成或未通过: {errs[0]}')
            for k in src:
                if k not in rows:
                    continue
                r = out.get(k)
                if r and 'delete' in r:
                    fd.write(json.dumps(dict(rows.pop(k), reason=r['delete']), ensure_ascii=False) + '\n'); deleted += 1
                elif r:
                    rows[k].update(pattern=r['pattern'], zh=r['zh'], review_status='reviewer-fixed', confidence='medium'); fixed += 1
                else:
                    rows[k].update(review_status='reviewer-ok', confidence='medium')
    with open(M / 'collocations.jsonl', 'w', encoding='utf-8') as f:
        for r in rows.values():
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f'collocations.jsonl {len(rows)} 条（审核改 {fixed}），删除 {deleted}')
