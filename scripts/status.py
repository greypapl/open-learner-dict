"""流水线状态：每个批次走到哪一步、下一步该派什么。

  python -I scripts/status.py            # 汇总 + 下一步建议
  python -I scripts/status.py --start writer B0006 B0007   # 派 agent 前打标记（防重复派发）

阶段：writer → reviewer → (有分歧) arbiter → merge
标记文件 work/raw/<批次>.<阶段>.started；超过 120 分钟仍无产出视为失败，可重派。
"""
import json, sys, time, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'work' / 'raw'
MERGED = ROOT / 'work' / 'merged'
STALE = 120 * 60

if len(sys.argv) > 2 and sys.argv[1] == '--start':
    stage = sys.argv[2]
    for b in sys.argv[3:]:
        (RAW / f'{b}.{stage}.started').write_text(str(time.time()))
    sys.exit(0)

batches = sorted(Path(p).name.split('.')[0] for p in glob.glob(str(ROOT / 'work' / 'batches' / 'B*.input.jsonl')))


def has(b, stage):
    return (RAW / f'{b}.{stage}.jsonl').exists()


def inflight(b, stage):
    m = RAW / f'{b}.{stage}.started'
    return m.exists() and not has(b, stage) and time.time() - float(m.read_text() or 0) < STALE


def n_disputes(b):
    p = RAW / f'{b}.disputes.jsonl'
    return sum(1 for l in open(p, encoding='utf-8') if l.strip()) if p.exists() else None


S = {k: [] for k in ['merged', 'need_merge', 'need_arbiter', 'need_disputes', 'need_review', 'need_write',
                     'run_writer', 'run_reviewer', 'run_arbiter']}
for b in batches:
    if (MERGED / f'{b}.jsonl').exists():
        S['merged'].append(b); continue
    if not has(b, 'writer'):
        S['run_writer' if inflight(b, 'writer') else 'need_write'].append(b); continue
    if not has(b, 'reviewer'):
        S['run_reviewer' if inflight(b, 'reviewer') else 'need_review'].append(b); continue
    d = n_disputes(b)
    if d is None:
        S['need_disputes'].append(b); continue
    if d > 0 and not has(b, 'arbiter'):
        S['run_arbiter' if inflight(b, 'arbiter') else 'need_arbiter'].append(b); continue
    S['need_merge'].append(b)

print(f"批次总数 {len(batches)}，已合并 {len(S['merged'])}")
for k in ['run_writer', 'run_reviewer', 'run_arbiter', 'need_disputes', 'need_merge', 'need_arbiter', 'need_review']:
    print(f"{k}: {len(S[k])} {' '.join(S[k][:12])}")
print(f"need_write: {len(S['need_write'])} 下一批: {' '.join(S['need_write'][:10])}")
