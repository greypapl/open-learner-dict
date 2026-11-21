"""短语层第二轮：定向补充（2026-11-20）。另有 make-themes（类别横扫 F 块）、audit-diff（查漏 G 块）。产出仍用 phrase.py check / dedup --append / merge。

  python -X utf8 -I scripts/phrase_more.py make-verbs [--top 10000] [--size 100]
      主词典前 N 词里带 v. 义项的动词 → work/phrase/V0001.in.txt（动词表）+ V0001.have.txt（已有的以这些动词开头的短语）
      prompt: prompts/phrase-verbs.md        写手输出 V0001.writer.txt
  python -X utf8 -I scripts/phrase_more.py make-idioms
      prompts/idiom-themes.txt 的主题，每块 4 个 → I0001.in.txt；已有习语写到 work/phrase/idioms-have.txt
      prompt: prompts/phrase-idioms.md       写手输出 I0001.writer.txt
  python -X utf8 -I scripts/phrase_more.py make-cands [--top 20000] [--size 3000]
      ECDICT 中 2–3 词、全部由前 N 常用词组成、且不在短语层里的条目 → K0001.in.txt
      prompt: prompts/phrase-triage.md       Sonnet 只输出保留的，末行 END <n>，写 K0001.out.txt
  python -X utf8 -I scripts/phrase_more.py triage-check
  python -X utf8 -I scripts/phrase_more.py make-strict      # K 保留词（初筛偏松）→ L0001.in.txt，prompt: prompts/phrase-triage2.md
  python -X utf8 -I scripts/phrase_more.py triage-check --strict
  python -X utf8 -I scripts/phrase_more.py make-compounds [--size 300]
      有 L 块就用 L 的保留词，否则用 K 的 → C0001.in.txt
      prompt: prompts/phrase-compound.md     写手输出 C0001.writer.txt
"""
import csv, glob, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
Q, M = ROOT / 'work/phrase', ROOT / 'work/merged'
csv.field_size_limit(10 ** 8)


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def entries_by_zipf():
    rows = []
    for f in glob.glob(str(M / 'B[0-9][0-9][0-9][0-9].jsonl')):
        for l in open(f, encoding='utf-8'):
            r = json.loads(l)
            rows.append((r.get('zipf') or 0, r['word'], r))
    rows.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [r for _, w, r in rows if w.isalpha() and w.islower()]


def have_phrases():
    hv = set()
    for p in list(Q.glob('*.writer.txt')) + list(Q.glob('*.supp.txt')) + list(Q.glob('R*.in.txt')):
        for l in open(p, encoding='utf-8'):
            if ' | ' in l:
                hv.add(l.split(' | ')[0].strip().lower())
    return hv


def write_chunks(prefix, items, size):
    for old in Q.glob(f'{prefix}*.in.txt'):
        old.unlink()
    for i in range(0, len(items), size):
        (Q / f'{prefix}{i // size + 1:04d}.in.txt').write_text('\n'.join(items[i:i + size]) + '\n', encoding='utf-8')
    return (len(items) - 1) // size + 1


cmd = sys.argv[1] if len(sys.argv) > 1 else ''
if cmd == 'make-verbs':
    top, size = arg('--top', 10000), arg('--size', 100)
    verbs = [r['word'] for r in entries_by_zipf()[:top] if any(s['pos'] == 'v.' for s in r['senses'])]
    n = write_chunks('V', verbs, size)
    hv = sorted(have_phrases())
    for i in range(n):
        vs = set(l.strip() for l in open(Q / f'V{i + 1:04d}.in.txt', encoding='utf-8'))
        (Q / f'V{i + 1:04d}.have.txt').write_text('\n'.join(p for p in hv if p.split()[0] in vs) + '\n', encoding='utf-8')
    print(len(verbs), 'verbs →', n, 'chunks')
elif cmd == 'make-idioms':
    themes = [l.strip() for l in open(ROOT / 'prompts/idiom-themes.txt', encoding='utf-8') if l.strip() and not l.startswith('#')]
    n = write_chunks('I', themes, 4)
    idioms = sorted(json.loads(l)['phrase'] for l in open(M / 'phrases.jsonl', encoding='utf-8') if json.loads(l)['type'] == 'idiom')
    (Q / 'idioms-have.txt').write_text('\n'.join(idioms) + '\n', encoding='utf-8')
    print(len(themes), 'themes →', n, 'chunks;', len(idioms), 'existing idioms')
elif cmd == 'make-themes':  # 类别横扫：prompts/phrase-themes.txt 每块 3 个 → F0001.in.txt，prompt: prompts/phrase-themes.md
    themes = [l.strip() for l in open(ROOT / 'prompts/phrase-themes.txt', encoding='utf-8') if l.strip() and not l.startswith('#')]
    print(len(themes), 'themes →', write_chunks('F', themes, 3), 'chunks')
elif cmd == 'audit-diff':  # 查漏：work/phrase/audit/*.txt（模型凭记忆列的常用清单）减去已有短语 → G0001.in.txt（每块 300），prompt: prompts/phrase-compound.md
    hv = have_phrases()
    norm = lambda x: re.sub(r'\b(someone|somebody)\b', 'sb', re.sub(r'\bsomething\b', 'sth', x.strip().lower()))
    hvn = {norm(h) for h in hv}
    miss, seen, tot = [], set(), 0
    for p in sorted((Q / 'audit').glob('*.txt')):
        for l in open(p, encoding='utf-8'):
            w = l.strip()
            if not w or ' ' not in w:
                continue
            tot += 1
            k = norm(w)
            if k not in hvn and k not in seen:
                seen.add(k); miss.append(w)
    print(f'清单 {tot} 条，缺 {len(miss)} 条 →', write_chunks('G', miss, arg('--size', 300)), 'G chunks')
elif cmd == 'make-cands':
    top, size = arg('--top', 20000), arg('--size', 3000)
    vocab = {r['word'] for r in entries_by_zipf()[:top]}
    hv = have_phrases()
    out, seen = [], set()
    for r in csv.DictReader(open(ROOT / 'sources/ecdict.csv', encoding='utf-8')):
        w = r['word'].strip()
        t = w.split()
        if (2 <= len(t) <= 3 and w.islower() and all(x in vocab for x in t) and w not in hv and w not in seen
                and re.fullmatch(r'[a-z ]+', w)):
            seen.add(w); out.append(w)
    print(len(out), 'candidates →', write_chunks('K', out, size), 'chunks')
elif cmd in ('triage-check', 'make-compounds', 'make-strict'):
    pre = 'L' if (cmd == 'make-compounds' and list(Q.glob('L*.in.txt'))) or '--strict' in sys.argv else 'K'
    keep, pend, bad = [], [], []
    for inp in sorted(Q.glob(f'{pre}*.in.txt')):
        words = [l.strip() for l in open(inp, encoding='utf-8') if l.strip()]
        out = inp.with_name(inp.name.replace('.in.', '.out.'))
        if not out.exists():
            pend.append(inp.name[:5]); continue
        lines = [l.strip() for l in open(out, encoding='utf-8') if l.strip()]
        ws = set(words)
        if not lines or lines[-1] != f'END {len(words)}':
            bad.append(f'{inp.name[:5]}: END 行不对'); continue
        k = [l for l in lines[:-1] if l in ws]
        if len(k) != len(lines) - 1:
            bad.append(f'{inp.name[:5]}: {len(lines) - 1 - len(k)} 行不在输入中（已忽略）')
        keep += k
    for b in bad:
        print('✗', b)
    print(f'保留 {len(keep)}；未完成 {len(pend)} 块 {" ".join(pend)}')
    if cmd == 'make-strict':  # 第二轮严筛：K 保留词 → L 块（prompt: prompts/phrase-triage2.md）
        if pend:
            sys.exit('还有 K 块未完成')
        print(write_chunks('L', keep, arg('--size', 2600)), 'L chunks')
    if cmd == 'make-compounds':
        if pend:
            sys.exit('还有 K 块未完成')
        print(write_chunks('C', keep, arg('--size', 300)), 'C chunks')
else:
    print(__doc__)
