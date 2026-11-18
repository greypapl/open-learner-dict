"""一次收尾 + 下一步建议（主会话每次 agent 完成后跑一次即可）。

  python -X utf8 -I scripts/tick.py [--upto B0202]

做的事（都不花额度）：
  1. 写手产物：jsonl 已存在但未校验的批次跑 validate（结果缓存在 <B>.writer.ok）
  2. 审核产物：reviewer.jsonl 存在且无 disputes 的批次跑 validate + disputes
  3. 分歧为 0、或仲裁已完成的批次直接 merge
  4. 打印：可派的审核组（连续 5 批已写未审）、可派的仲裁组（待仲裁批次 ≥ 10 或无在途写手/审核时全部）、下一组可写批次
"""
import subprocess, sys, json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, MERGED, BATCH = ROOT / 'work' / 'raw', ROOT / 'work' / 'merged', ROOT / 'work' / 'batches'
PY = [sys.executable, '-X', 'utf8', '-I']
STALE = 120 * 60
upto = sys.argv[sys.argv.index('--upto') + 1] if '--upto' in sys.argv else None
bs = sorted(p.name.split('.')[0] for p in BATCH.glob('B*.input.jsonl'))
if upto:
    bs = [b for b in bs if b <= upto]


def ex(b, s):
    return (RAW / f'{b}.{s}').exists()


def started(b, stage):
    m = RAW / f'{b}.{stage}.started'
    return m.exists() and time.time() - float(m.read_text() or 0) < STALE


def node_ok(f, inp=None):
    cmd = ['node', str(ROOT / 'scripts/validate.js'), str(f)] + (['--input', str(inp)] if inp else [])
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    return r.returncode == 0, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]


def ndisp(b):
    p = RAW / f'{b}.disputes.jsonl'
    return sum(1 for l in p.open(encoding='utf-8') if l.strip()) if p.exists() else None


log, merged_now = [], []
for b in bs:
    if (MERGED / f'{b}.jsonl').exists():
        continue
    if ex(b, 'writer.jsonl') and not ex(b, 'writer.ok'):
        ok, msg = node_ok(RAW / f'{b}.writer.jsonl', BATCH / f'{b}.input.jsonl')
        if ok:
            (RAW / f'{b}.writer.ok').write_text('1')
        else:
            log.append(f'✗ {b} writer: {msg}')
    grp = (RAW / f'{b}.reviewer.group').read_text().split() if ex(b, 'reviewer.group') else [b]
    if ex(b, 'reviewer.jsonl') and ndisp(b) is None and all(ex(g, 'reviewer.jsonl') for g in grp):
        ok, msg = node_ok(RAW / f'{b}.reviewer.jsonl', BATCH / f'{b}.input.jsonl')
        if ok:
            subprocess.run(PY + [str(ROOT / 'scripts/pipeline.py'), 'disputes', b], capture_output=True)
        else:
            log.append(f'✗ {b} reviewer: {msg}')
    d = ndisp(b)
    if d is not None and (d == 0 or ex(b, 'arbiter.jsonl')):
        if d and not node_ok(RAW / f'{b}.arbiter.jsonl')[0]:
            log.append(f'✗ {b} arbiter 校验失败')
            continue
        r = subprocess.run(PY + [str(ROOT / 'scripts/pipeline.py'), 'merge', b], capture_output=True, text=True, encoding='utf-8')
        if "'missing_arbiter': 0" not in r.stdout:
            log.append(f'⚠ {b} merge: {r.stdout.strip()}')
        merged_now.append(b)

state = {}
for b in bs:
    if (MERGED / f'{b}.jsonl').exists():
        s = 'merged'
    elif not ex(b, 'writer.ok'):
        s = 'writing' if started(b, 'writer') else 'todo'
    elif not ex(b, 'reviewer.jsonl'):
        s = 'reviewing' if started(b, 'reviewer') else 'need_review'
    elif ndisp(b) and not ex(b, 'arbiter.jsonl'):
        s = 'arbitrating' if started(b, 'arbiter') else 'need_arbiter'
    else:
        s = '?'
    state[b] = s
cnt = {}
for s in state.values():
    cnt[s] = cnt.get(s, 0) + 1
for x in log:
    print(x)
if merged_now:
    print('本次合并:', ' '.join(merged_now))
print('状态:', ' '.join(f'{k}={v}' for k, v in sorted(cnt.items())))
need_rev = [b for b in bs if state[b] == 'need_review']
busy = any(state[b] in ('writing', 'reviewing') for b in bs)
groups = [need_rev[i:i + 5] for i in range(0, len(need_rev), 5)]
groups = [g for g in groups if len(g) == 5 or not any(state[b] == 'writing' for b in bs)]
if groups:
    print('可派审核:', ' | '.join(' '.join(g) for g in groups))
need_arb = [b for b in bs if state[b] == 'need_arbiter']
n = sum(ndisp(b) for b in need_arb)
if need_arb and (len(need_arb) >= 10 or not busy):
    print(f'可派仲裁（{n} 条）:', ' '.join(need_arb))
elif need_arb:
    print(f'待仲裁攒批中: {len(need_arb)} 批 / {n} 条')
todo = [b for b in bs if state[b] == 'todo']
if todo:
    print('下一组写手:', ' '.join(todo[:3]))
print('在途: 写', sum(state[b] == 'writing' for b in bs) // 1, '批 · 审', sum(state[b] == 'reviewing' for b in bs), '批 · 仲裁', sum(state[b] == 'arbitrating' for b in bs), '批')
