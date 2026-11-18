"""初筛完成后，选出交给 Opus 的最终词头 → work/selected.jsonl，并切 200 词批次 → work/batches/B<序号>.input.jsonl

顺序：前 1000 名（免筛）→ 主池初筛保留（按 wordfreq 排名）→ 尾部 K1（按旧表排名）→ 尾部 K2。
截取 --target 个（默认 105000，给 Opus 再跳过留 5% 余量）。

  python -I scripts/select_words.py [--target 105000] [--size 200]
"""
import json, glob, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W = ROOT / 'work'
ap = argparse.ArgumentParser()
ap.add_argument('--target', type=int, default=105000)
ap.add_argument('--size', type=int, default=200)
a = ap.parse_args()

rows = [json.loads(l) for l in open(W / 'headwords.jsonl', encoding='utf-8')]
code = {}
for f in glob.glob(str(W / 'screen' / 'S*.out.tsv')):
    for l in open(f, encoding='utf-8'):
        p = l.rstrip('\n').split('\t')
        code[p[0]] = p[1]

missing = [r['id'] for r in rows if r['rank'] > 1000 and r['id'] not in code]
if missing:
    raise SystemExit(f'还有 {len(missing)} 个候选未初筛（例 {missing[:3]}），先跑完初筛')

head = [r for r in rows if r['rank'] <= 1000]
main = [r for r in rows if r['rank'] > 1000 and r['tier'] == 'main' and code[r['id']] in ('K1', 'K2')]
t1 = [r for r in rows if r['tier'] == 'tail' and code[r['id']] == 'K1']
t2 = [r for r in rows if r['tier'] == 'tail' and code[r['id']] == 'K2']
sel = (head + main + t1 + t2)[:a.target]
print(f'head={len(head)} main_keep={len(main)} tail_K1={len(t1)} tail_K2={len(t2)} → selected={len(sel)}')

FIELDS = ['id', 'rank', 'word', 'kind', 'exam_tags', 'inflections', 'ipa_us_cmu']
with open(W / 'selected.jsonl', 'w', encoding='utf-8') as f:
    for i, r in enumerate(sel, 1):
        f.write(json.dumps({**r, 'sel_order': i, 'screen': code.get(r['id'], 'head')}, ensure_ascii=False) + '\n')
(W / 'batches').mkdir(exist_ok=True)
n = 0
for i in range(0, len(sel), a.size):
    n += 1
    with open(W / 'batches' / f'B{n:04d}.input.jsonl', 'w', encoding='utf-8') as f:
        for r in sel[i:i + a.size]:
            f.write(json.dumps({k: r[k] for k in FIELDS}, ensure_ascii=False) + '\n')
print(f'{n} 个批次 B0001–B{n:04d}')
