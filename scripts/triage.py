"""尾部初筛（triage）：先让模型只挑出值得收录的词，再把留下的词重新切成写手批次。

  python -X utf8 -I scripts/triage.py make [--size 2000]   # 原尾部 B0343–B0758 → work/triage/T0001.in.txt …
  python -X utf8 -I scripts/triage.py check                # 检查 T*.out.txt（Sonnet）+ X*.out.txt（Opus），统计并集
  python -X utf8 -I scripts/triage.py rebatch [--first 343] # 保留词 → 新 B 批次；原尾部输入移到 work/batches/tail-raw/
                                                            # 未保留的词记到 work/merged/triage-skips.jsonl（skip:too-rare）

prompt: prompts/triage.md
"""
import json, sys, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
B, T, M = ROOT / 'work/batches', ROOT / 'work/triage', ROOT / 'work/merged'
RAW_TAIL = B / 'tail-raw'
FIRST_TAIL = 343


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def tail_rows():
    src = RAW_TAIL if RAW_TAIL.exists() else B
    rows = []
    for p in sorted(src.glob('B*.input.jsonl')):
        if int(p.name[1:5]) >= FIRST_TAIL:
            rows += [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
    return rows


def chunks():
    return sorted(T.glob('T*.in.txt'))


def read_union(inp):
    a, ma = read_out(inp, 'T')
    b, mb = read_out(inp, 'X')
    if a is None or b is None:
        return None, ma if a is None else mb
    return a | b, 'ok'


def read_out(inp, prefix='T'):
    """一块的初筛结果。T = Sonnet，X = Opus；最终保留取两者并集（triage-v1）。"""
    out = inp.with_name(prefix + inp.name[1:].replace('.in.', '.out.'))
    if not out.exists():
        return None, 'missing'
    words = [l.strip() for l in open(inp, encoding='utf-8') if l.strip()]
    lines = [l.strip() for l in open(out, encoding='utf-8') if l.strip()]
    if not lines or lines[-1] != f'END {len(words)}':
        return None, f'bad END line: {lines[-1] if lines else "(empty)"}'
    keep = lines[:-1]
    ws = set(words)
    bad = [w for w in keep if w not in ws]
    if bad:
        return None, f'{len(bad)} words not in input, e.g. {bad[:3]}'
    return set(keep), 'ok'


cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
if cmd == 'make':
    size = arg('--size', 2000)
    T.mkdir(parents=True, exist_ok=True)
    rows = tail_rows()
    for i in range(0, len(rows), size):
        p = T / f'T{i // size + 1:04d}.in.txt'
        p.write_text('\n'.join(r['word'] for r in rows[i:i + size]) + '\n', encoding='utf-8')
    print(len(rows), 'words →', len(chunks()), 'chunks')
elif cmd == 'check':
    tot = kept = 0
    for inp in chunks():
        keep, msg = read_union(inp)
        n = sum(1 for l in open(inp, encoding='utf-8') if l.strip())
        if keep is None:
            if msg != 'missing':
                print(f'✗ {inp.name}: {msg}')
            continue
        tot += n
        kept += len(keep)
        print(f'{inp.name[:5]} {len(keep):5d}/{n} ({100 * len(keep) / n:.0f}%)')
    pend = [p.name[1:5] for p in chunks() if read_union(p)[1] == 'missing']
    print(f'done {tot} words, keep {kept} ({100 * kept / max(1, tot):.1f}%); pending {len(pend)}: {" ".join(pend)}')
elif cmd == 'rebatch':
    first = arg('--first', FIRST_TAIL)
    res = [read_union(p) for p in chunks()]
    if any(k is None for k, _ in res):
        sys.exit('not all chunks done/valid; run check')
    keepset = set().union(*[k for k, _ in res])
    rows = tail_rows()
    if not RAW_TAIL.exists():
        RAW_TAIL.mkdir()
        for p in sorted(B.glob('B*.input.jsonl')):
            if int(p.name[1:5]) >= FIRST_TAIL:
                shutil.move(str(p), RAW_TAIL / p.name)
    for p in B.glob('B*.input.jsonl'):  # 清掉上次 rebatch 生成的
        if int(p.name[1:5]) >= first:
            p.unlink()
    kept = [r for r in rows if r['word'] in keepset]
    for i in range(0, len(kept), 200):
        with open(B / f'B{first + i // 200:04d}.input.jsonl', 'w', encoding='utf-8') as f:
            for r in kept[i:i + 200]:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
    with open(M / 'triage-skips.jsonl', 'w', encoding='utf-8') as f:
        for r in rows:
            if r['word'] not in keepset:
                f.write(json.dumps({'id': r['id'], 'word': r['word'], 'skip': 'too-rare', 'by': 'triage-v1'}, ensure_ascii=False) + '\n')
    print(f'{len(rows)} tail words → keep {len(kept)} → B{first:04d}–B{first + (len(kept) - 1) // 200:04d}; '
          f'{len(rows) - len(kept)} → triage-skips.jsonl')
