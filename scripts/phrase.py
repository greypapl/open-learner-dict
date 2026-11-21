"""短语层（phrase-v1）：从常用词出发列出短语动词、习语、固定短语、开放式复合词。

  python -X utf8 -I scripts/phrase.py make [--top 6000] [--size 100]   # 主词典按 zipf 取前 N 个词头 → work/phrase/Q0001.in.txt …
  python -X utf8 -I scripts/phrase.py check [Q0001 …] [--role writer|supp|reviewer]   # 校验 Q*.writer.txt / Q*.supp.txt（补写）
  python -X utf8 -I scripts/phrase.py dedup [--size 400] [--append]    # 汇总全部写手输出、去重 → 审核块 work/phrase/R0001.in.txt …
  python -X utf8 -I scripts/phrase.py check R0001 … --role reviewer    # 校验审核输出（只含改正行或 delete 行）
  python -X utf8 -I scripts/phrase.py merge                            # 应用审核 → work/merged/phrases.jsonl + phrase-deletes.jsonl

prompts: prompts/phrase-writer.md, prompts/phrase-reviewer.md
"""
import glob, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
Q, M = ROOT / 'work/phrase', ROOT / 'work/merged'
TYPES = {'phrv', 'idiom', 'phrase', 'compound'}
POS = r'(n\.|v\.|adj\.|adv\.|prep\.|conj\.|pron\.|det\.|int\.|num\.)'
SENSE = re.compile(r'^' + POS + r'(.+?) = (.+?)(?:\s*\[([^\]]+)\])?$')
TAGS = {'formal', 'informal', 'slang', 'dated', 'literary', 'uk', 'us', 'offensive-mild', 'offensive-strong'}
LEVELS = {'A1', 'A2', 'B1', 'B2', 'C1', 'C2'}
BAD = re.compile(r'[()（）；。;\[\]a-zA-Z]')


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def parse(line):
    f = [x.strip() for x in line.split(' | ')]
    if len(f) != 5:
        raise ValueError(f'字段数 {len(f)} ≠ 5')
    ph, typ, senses_s, lvl, flags = f
    if ' ' not in ph or not re.fullmatch(r"[A-Za-z][A-Za-z' .,!?-]*[A-Za-z.!?]", ph):
        raise ValueError(f'短语不合规: {ph}')
    if typ not in TYPES:
        raise ValueError(f'类型非法: {typ}')
    if lvl not in LEVELS:
        raise ValueError(f'级别非法: {lvl}')
    fl = [] if flags == '-' else flags.split()
    if any(x not in ('low', 'nokid') for x in fl):
        raise ValueError(f'标记非法: {flags}')
    parts = [p.strip() for p in senses_s.split(' ; ')]
    if not 1 <= len(parts) <= 4:
        raise ValueError('义项数应为 1–4')
    senses = []
    for p in parts:
        m = SENSE.match(p)
        if not m:
            raise ValueError(f'义项格式错: {p}')
        zh = [z.strip() for z in m.group(2).split(',') if z.strip()]
        if not 1 <= len(zh) <= 4 or any(len(z) > 12 or BAD.search(z) for z in zh):
            raise ValueError(f'中文不合规: {m.group(2)}')
        en = m.group(3).strip()
        if len(en.split()) > 12 or ' = ' in en:
            raise ValueError(f'英文简释过长或含 = : {en}')
        tags = [t.strip() for t in (m.group(4) or '').split(',') if t.strip()]
        for t in tags:
            if t not in TAGS and not t.startswith('domain:'):
                raise ValueError(f'标签非法: {t}')
        senses.append({'pos': m.group(1), 'zh': zh, 'en_short': en, 'tags': tags})
    return {'phrase': ph, 'type': typ, 'senses': senses, 'level': lvl, 'flags': fl}


DEL = re.compile(r'^(.+?) \| delete:(free|rare|proper|wrong|variant)(=.+)?$')


def read(path, allow_delete=False):
    res, errs = [], []
    for i, l in enumerate(open(path, encoding='utf-8'), 1):
        if not l.strip():
            continue
        try:
            m = DEL.match(l.strip()) if allow_delete else None
            if m:
                res.append({'phrase': m.group(1).strip(), 'delete': m.group(2), 'keep': (m.group(3) or '')[1:]})
                continue
            res.append(parse(l.rstrip('\n')))
        except ValueError as e:
            errs.append(f'第 {i} 行: {e} :: {l.strip()[:80]}')
    return res, errs


cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
if cmd == 'make':
    top, size = arg('--top', 6000), arg('--size', 100)
    Q.mkdir(parents=True, exist_ok=True)
    rows = []
    for f in glob.glob(str(M / 'B[0-9][0-9][0-9][0-9].jsonl')):
        for l in open(f, encoding='utf-8'):
            r = json.loads(l)
            rows.append((r.get('zipf') or 0, r['word']))
    words = [w for _, w in sorted(rows, reverse=True) if w.isalpha() and w.islower()][:top]
    for i in range(0, len(words), size):
        (Q / f'Q{i // size + 1:04d}.in.txt').write_text('\n'.join(words[i:i + size]) + '\n', encoding='utf-8')
    print(len(words), 'headwords →', (len(words) - 1) // size + 1, 'chunks')
elif cmd == 'check':
    role = arg('--role', 'writer')
    pre = 'R' if role == 'reviewer' else 'Q'
    names = [a for a in sys.argv[2:] if re.fullmatch(r'[A-Z]\d{4}', a)] or sorted(p.name[:5] for p in Q.glob(pre + '*.in.txt'))
    tot, pend = 0, []
    for n in names:
        p = Q / f'{n}.{role}.txt'
        if not p.exists():
            pend.append(n); continue
        res, errs = read(p, role == 'reviewer')
        if role == 'reviewer' and not errs:
            src = {r['phrase'] for r in read(Q / f'{n}.in.txt')[0]}
            errs = [f'不在输入中: {r["phrase"]}' for r in res if r['phrase'] not in src]
        if errs:
            print(f'✗ {n}: {len(errs)} 处问题'); [print('  ', e) for e in errs[:20]]; continue
        dup = len(res) - len({r['phrase'].lower() for r in res})
        tot += len(res)
        from collections import Counter
        print(f'✓ {n}: {len(res)} 条（{dict(Counter(r.get("type", "delete:" + r.get("delete", "")) for r in res))}）'
              + (f'，块内重复 {dup}' if dup else ''))
    print(f'合计 {tot} 条；未完成 {len(pend)} 块 {" ".join(pend)}')
elif cmd == 'dedup':
    size = arg('--size', 400)
    append = '--append' in sys.argv  # 保留已审核的 R 块，只把新短语切成后续 R 块
    seen, out = set(), []
    if append:
        for p in Q.glob('R*.in.txt'):
            seen |= {r['phrase'].lower() for r in read(p)[0]}
    for p in sorted(list(Q.glob('[QVICFG]*.writer.txt')) + list(Q.glob('Q*.supp.txt'))):
        res, errs = read(p)
        if errs:
            sys.exit(f'{p.name} 未通过校验')
        lines = [l.rstrip('\n') for l in open(p, encoding='utf-8') if l.strip()]
        for r, l in zip(res, lines):
            k = r['phrase'].lower()
            if k not in seen:
                seen.add(k); out.append(l)
    start = len(list(Q.glob('R*.in.txt'))) if append else 0
    if not append:
        for old in Q.glob('R*.in.txt'):
            old.unlink()
    for i in range(0, len(out), size):
        (Q / f'R{start + i // size + 1:04d}.in.txt').write_text('\n'.join(out[i:i + size]) + '\n', encoding='utf-8')
    print(len(out), 'unique phrases →', (len(out) - 1) // size + 1, 'review chunks')
elif cmd == 'merge':
    n_ok = n_fix = n_del = 0
    with open(M / 'phrases.jsonl', 'w', encoding='utf-8') as fo, open(M / 'phrase-deletes.jsonl', 'w', encoding='utf-8') as fd:
        for p in sorted(Q.glob('R*.in.txt')):
            n = p.name[:5]
            rv = Q / f'{n}.reviewer.txt'
            if not rv.exists():
                sys.exit(f'{n} 缺审核输出')
            fix, errs = read(rv, True)
            if errs:
                sys.exit(f'{n} 审核输出未通过校验')
            fixd = {r['phrase']: r for r in fix}
            for r in read(p)[0]:
                f = fixd.get(r['phrase'])
                if f and 'delete' in f:
                    fd.write(json.dumps({'phrase': r['phrase'], 'reason': f['delete'], 'keep': f['keep'], 'writer': r},
                                        ensure_ascii=False) + '\n'); n_del += 1
                    continue
                status = 'reviewer-fixed' if f else 'reviewer-ok'
                e = f or r
                n_fix += bool(f); n_ok += not f
                fo.write(json.dumps(dict(e, layer='phrase', confidence='medium', review_status=status, source='phrase-v1'),
                                    ensure_ascii=False) + '\n')
    print(f'phrases.jsonl {n_ok + n_fix} 条（审核改 {n_fix}），删除 {n_del}')
