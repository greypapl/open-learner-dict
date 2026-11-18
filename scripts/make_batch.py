"""切批次：从 work/headwords.jsonl 生成写手输入 work/batches/<name>.input.jsonl

用法:
  python -I scripts/make_batch.py --pilot            # 200 词分层试点 → P0001
  python -I scripts/make_batch.py --from 1 --to 1000 --size 200   # 按排名切成若干批 B<起始排名>

写手只拿到事实字段，不含任何 ECDICT 释义。
"""
import json, random, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W = ROOT / 'work'
FIELDS = ['id', 'rank', 'word', 'kind', 'exam_tags', 'inflections', 'ipa_us_cmu']

ap = argparse.ArgumentParser()
ap.add_argument('--pilot', action='store_true')
ap.add_argument('--from', dest='start', type=int)
ap.add_argument('--to', dest='end', type=int)
ap.add_argument('--size', type=int, default=200)
a = ap.parse_args()

rows = [json.loads(l) for l in open(W / 'headwords.jsonl', encoding='utf-8')]
(W / 'batches').mkdir(parents=True, exist_ok=True)


def dump(name, items):
    p = W / 'batches' / f'{name}.input.jsonl'
    with open(p, 'w', encoding='utf-8') as f:
        for r in items:
            f.write(json.dumps({k: r[k] for k in FIELDS}, ensure_ascii=False) + '\n')
    print(p.relative_to(ROOT), len(items))


if a.pilot:
    rnd = random.Random(20261114)
    bands = [(1, 1000), (1001, 5000), (5001, 20000), (20001, 50000), (50001, 105000)]
    pick = []
    for lo, hi in bands:
        pick += rnd.sample([r for r in rows if lo <= r['rank'] <= hi], 40)
    pick.sort(key=lambda r: r['rank'])
    # 分成 5 个 40 词的小批，方便并行
    for i in range(5):
        dump(f'P{i + 1:04d}', pick[i::5])
else:
    sel = [r for r in rows if a.start <= r['rank'] <= a.end]
    for i in range(0, len(sel), a.size):
        chunk = sel[i:i + a.size]
        dump(f"B{chunk[0]['rank']:06d}", chunk)
