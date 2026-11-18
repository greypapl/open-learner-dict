"""切初筛分片：work/screen/S<序号>.in.tsv

  python -I scripts/make_screen.py --size 3000            # 全部候选（排名 >1000）
  python -I scripts/make_screen.py --pilot                 # 用 200 个试点词做校准 → work/screen/CAL.in.tsv
  python -I scripts/make_screen.py --summary               # 汇总已完成分片

前 1000 名试点保留率 100%，不做初筛。
"""
import json, re, argparse, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W = ROOT / 'work'
S = W / 'screen'
ap = argparse.ArgumentParser()
ap.add_argument('--size', type=int, default=3000)
ap.add_argument('--pilot', action='store_true')
ap.add_argument('--summary', action='store_true')
a = ap.parse_args()
S.mkdir(parents=True, exist_ok=True)

rows = [json.loads(l) for l in open(W / 'headwords.jsonl', encoding='utf-8')]
words = {r['word'].lower() for r in rows}


def hint(r):
    h = []
    if r['kind'] != 'word':
        h.append(r['kind'])
    if r.get('lemma_of'):
        h.append(f"infl-of:{r['lemma_of']}")
    w = r['word']
    for suf, rep in (('ies', 'y'), ('es', ''), ('s', ''), ('ed', ''), ('ed', 'e'), ('ing', ''), ('ing', 'e'), ('er', ''), ('est', '')):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            stem = w[:-len(suf)] + rep
            if stem in words and stem != w:
                h.append(f'stem?:{stem}')
                break
    return ' '.join(h)


def dump(name, items):
    p = S / f'{name}.in.tsv'
    p.write_text(''.join(f"{r['id']}\t{r['word']}\t{hint(r)}\n" for r in items), encoding='utf-8')
    return p


if a.summary:
    by = {r['id']: r for r in rows}
    stat = {'main': {}, 'tail': {}}
    for f in sorted(glob.glob(str(S / 'S*.out.tsv'))):
        for l in open(f, encoding='utf-8'):
            p = l.rstrip('\n').split('\t')
            code = p[1] if p[1] != 'S' else 'S:' + p[2]
            t = stat[by[p[0]]['tier']]
            t[code] = t.get(code, 0) + 1
    for k, v in stat.items():
        tot = sum(v.values())
        keep = v.get('K1', 0) + v.get('K2', 0)
        print(k, tot, 'keep', keep, f'({keep / tot:.0%})' if tot else '', dict(sorted(v.items())))
elif a.pilot:
    ids = [l.split('"id": "')[1][:7] for f in sorted(glob.glob(str(W / 'batches' / 'P*.input.jsonl')))
           for l in open(f, encoding='utf-8')]
    by = {r['id']: r for r in rows}
    print(dump('CAL', [by[i] for i in sorted(ids)]))
else:
    todo = [r for r in rows if r['rank'] > 1000]
    for i in range(0, len(todo), a.size):
        dump(f'S{i // a.size + 1:03d}', todo[i:i + a.size])
    print(f'{len(todo)} 个候选 → {(len(todo) + a.size - 1) // a.size} 片')
