"""简释层审核（gloss-review-v1）：Opus 逐条看冷僻词的中文简释，只输出要改或要删的行。

  python -X utf8 -I scripts/gloss_review.py make [--version 0.10.0] [--size 2000]   # 发布包 gloss.jsonl → work/gloss-review/G001.in.txt
  python -X utf8 -I scripts/gloss_review.py check [G001 …]
  python -X utf8 -I scripts/gloss_review.py apply                                    # → work/merged/gloss-review.jsonl（release.py 读取）

输入行：sense_id | word | pos | 中文 | 领域标签
输出（只写要改的）：sense_id | pos | 改后中文（1–3 个，用 , 分隔）
                   或 <词条 id> | delete | 原因（不是真实英语词、拼写错误、和别的词条重复）
prompt: prompts/gloss-review.md
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D, M = ROOT / 'work/gloss-review', ROOT / 'work/merged'
POS = {'n.', 'v.', 'adj.', 'adv.', 'prep.', 'conj.', 'pron.', 'det.', 'int.', 'num.', 'aux.', 'abbr.'}
BAD = re.compile(r'[()（）；;。\[\]]')


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def names():
    sel = [a for a in sys.argv[2:] if re.fullmatch(r'G\d{3}', a)]
    return sel or sorted(p.name[:4] for p in D.glob('G*.in.txt'))


def read(n):
    src, ids = {}, set()
    for l in open(D / f'{n}.in.txt', encoding='utf-8'):
        f = l.rstrip('\n').split(' | ')
        src[f[0]] = f; ids.add(f[0].rsplit('.', 1)[0])
    o = D / f'{n}.reviewer.txt'
    if not o.exists():
        return None, None, []
    fix, dele, errs = {}, {}, []
    for i, l in enumerate(open(o, encoding='utf-8'), 1):
        if not l.strip():
            continue
        f = [x.strip() for x in l.split(' | ')]
        if len(f) == 5 and f[0] in src:  # 整行抄回来的
            f = [f[0], f[2], f[3]]
        if len(f) == 3 and f[1] == 'delete' and f[0] in ids:
            dele[f[0]] = f[2]; continue
        if len(f) != 3 or f[0] not in src:
            errs.append(f'{o.name} 第 {i} 行格式错或 id 不在输入中：{l.strip()[:60]}'); continue
        zs = [z.strip() for z in f[2].split(',') if z.strip()]
        if f[1] not in POS:
            errs.append(f'{o.name} 第 {i} 行词性非法：{f[1]}'); continue
        if not 1 <= len(zs) <= 3 or any(BAD.search(z) or len(z) > 16 or not re.search(r'[㐀-鿿]', z) for z in zs):
            errs.append(f'{o.name} 第 {i} 行中文不合规（1–3 个，每个 ≤16 字、不带括号和；。）：{f[2][:40]}'); continue
        if f[1] != src[f[0]][2] or ', '.join(zs) != src[f[0]][3]:
            fix[f[0]] = {'pos': f[1], 'zh': zs}
    return fix, dele, errs


cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
if cmd == 'make':
    D.mkdir(parents=True, exist_ok=True)
    ver, size = arg('--version', '0.10.0'), arg('--size', 2000)
    L = [f"{s['sense_id']} | {r['word']} | {s['pos']} | {s['zh']} | {', '.join(s['register']) or '-'}"
         for r in (json.loads(l) for l in open(ROOT / 'release' / ver / 'jsonl/gloss.jsonl', encoding='utf-8')) for s in r['senses']]
    if list(D.glob('G*.in.txt')):
        sys.exit('已经切过块了；要重切先删掉 work/gloss-review/G*.in.txt')
    for i in range(0, len(L), size):
        (D / f'G{i // size + 1:03d}.in.txt').write_text('\n'.join(L[i:i + size]) + '\n', encoding='utf-8')
    print(f'{len(L)} 个义项 → {(len(L) - 1) // size + 1} 块')
elif cmd in ('check', 'apply'):
    allfix, alldel, pend, bad = {}, {}, [], 0
    for n in names():
        fix, dele, errs = read(n)
        if fix is None:
            pend.append(n); continue
        for e in errs[:15]:
            print('✗', e)
        bad += len(errs)
        print(f'{n}: 改 {len(fix)}，删 {len(dele)}，格式问题 {len(errs)}')
        allfix.update(fix); alldel.update(dele)
    print(f'合计 改 {len(allfix)}，删 {len(alldel)}；未完成 {" ".join(pend) or "无"}')
    if cmd == 'apply':
        if pend or bad:
            sys.exit('还有未完成或格式问题')
        reviewed = set()
        for n in names():
            reviewed |= {l.split(' | ')[0].rsplit('.', 1)[0] for l in open(D / f'{n}.in.txt', encoding='utf-8')}
        with open(M / 'gloss-review.jsonl', 'w', encoding='utf-8', newline='\n') as f:
            for k in sorted(allfix):
                f.write(json.dumps({'sense_id': k, **allfix[k]}, ensure_ascii=False) + '\n')
            for k in sorted(alldel):
                f.write(json.dumps({'delete': k, 'reason': alldel[k]}, ensure_ascii=False) + '\n')
            f.write(json.dumps({'reviewed_ids': sorted(reviewed)}, ensure_ascii=False) + '\n')
        print(f'work/merged/gloss-review.jsonl：改 {len(allfix)}，删 {len(alldel)}，审过 {len(reviewed)} 个词条')
