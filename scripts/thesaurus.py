"""同义词 / 反义词（thesaurus-v1）：按义项给常用同义词、反义词，只收词典里已有的词条或短语。

  python -X utf8 -I scripts/thesaurus.py make [--top 10000] [--max-level C1] [--size 400]   # → work/thesaurus/S0001.in.txt（增量）
  python -X utf8 -I scripts/thesaurus.py check [S0001 …]
  python -X utf8 -I scripts/thesaurus.py review-make [--size 2500]                         # → work/thesaurus/R0001.in.txt（增量）
  python -X utf8 -I scripts/thesaurus.py review-check [R0001 …]
  python -X utf8 -I scripts/thesaurus.py apply                                             # → work/merged/thesaurus.jsonl

输入行：sense_id | word | pos | level | 中文释义 | en_short
写手输出（每行都写）：sense_id | 同义词, … | 反义词, …        没有就写 -
审核输出（只写要改的）：同样格式
prompts: prompts/thesaurus-writer.md, prompts/thesaurus-reviewer.md
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D, M = ROOT / 'work/thesaurus', ROOT / 'work/merged'
VER = sys.argv[sys.argv.index('--version') + 1] if '--version' in sys.argv else '0.10.0'
REL = ROOT / 'release' / VER / 'jsonl'


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def names(p):
    sel = [a for a in sys.argv[2:] if re.fullmatch(p + r'\d{4}', a)]
    return sel or sorted(x.name[:5] for x in D.glob(f'{p}*.in.txt'))


def inputs(n):
    return {l.split(' | ')[0]: l.rstrip('\n').split(' | ') for l in open(D / f'{n}.in.txt', encoding='utf-8')}


_known = None


def known():  # 主词典、简释层的词头和短语层的短语（小写）
    global _known
    if _known is None:
        _known = set()
        for f, k in (('core.jsonl', 'word'), ('gloss.jsonl', 'word'), ('phrases.jsonl', 'phrase')):
            _known |= {json.loads(l)[k].lower() for l in open(REL / f, encoding='utf-8')}
    return _known


def items(s):
    return [] if s.strip() in ('-', '') else [x.strip() for x in s.split(',') if x.strip()]


def parse(line, src):
    f = [x.strip() for x in line.split(' | ')]
    if len(f) != 3:
        raise ValueError(f'字段数 {len(f)} ≠ 3')
    sid, syn, ant = f[0], items(f[1]), items(f[2])
    if sid not in src:
        raise ValueError(f'sense_id 不在输入中: {sid}')
    w = src[sid][1].lower()
    if len(syn) > 4 or len(ant) > 2:
        raise ValueError('同义词最多 4 个、反义词最多 2 个')
    for x in syn + ant:
        if x.lower() == w:
            raise ValueError(f'不能列词头本身: {x}')
        if x.lower() not in known():
            raise ValueError(f'「{x}」不是词典里的词条或短语（换一个常用的，或删掉）')
    if len({x.lower() for x in syn + ant}) != len(syn + ant):
        raise ValueError('有重复')
    return sid, syn, ant


def read(n, suffix, src=None):
    src = src or inputs(n)
    o = D / f'{n}.{suffix}.txt'
    if not o.exists():
        return src, None, []
    res, errs = {}, []
    for i, l in enumerate(open(o, encoding='utf-8'), 1):
        if not l.strip():
            continue
        try:
            sid, syn, ant = parse(l, src)
            res[sid] = (syn, ant)
        except ValueError as e:
            errs.append(f'{o.name} 第 {i} 行 {e}：{l.strip()[:70]}')
    return src, res, errs


cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
if cmd == 'make':
    D.mkdir(parents=True, exist_ok=True)
    top, maxlv, size = arg('--top', 10000), arg('--max-level', 'C1'), arg('--size', 400)
    rows = sorted((json.loads(l) for l in open(REL / 'core.jsonl', encoding='utf-8')), key=lambda r: r['rank'])
    done = set()
    for p in D.glob('S*.in.txt'):
        done |= set(inputs(p.name[:5]))
    L = [f"{s['sense_id']} | {r['word']} | {s['pos']} | {r['level']} | {s['zh']} | {s['en_short']}"
         for r in rows if r['rank'] <= top or r['level'] <= maxlv for s in r['senses'] if s['sense_id'] not in done]
    if not L:
        sys.exit('没有新的义项')
    start, chunks, cur = len(list(D.glob('S*.in.txt'))), [], []
    for l in L:  # 同一个词的义项不拆开
        if len(cur) >= size and l.split(' | ')[0].split('.')[0] != cur[-1].split(' | ')[0].split('.')[0]:
            chunks.append(cur); cur = []
        cur.append(l)
    chunks.append(cur)
    for j, c in enumerate(chunks, start + 1):
        (D / f'S{j:04d}.in.txt').write_text('\n'.join(c) + '\n', encoding='utf-8')
    print(f'新义项 {len(L)} 个 → {len(chunks)} 块 S{start + 1:04d}–S{start + len(chunks):04d}')
elif cmd == 'check':
    for n in names('S'):
        src, res, errs = read(n, 'out')
        if res is None:
            print(f'{n}: 未完成'); continue
        miss = [s for s in src if s not in res]
        for e in errs[:20]:
            print('✗', e)
        if miss:
            print(f'✗ {n} 缺 {len(miss)} 个义项：{" ".join(miss[:10])}')
        ns = sum(1 for v in res.values() if v[0]); na = sum(1 for v in res.values() if v[1])
        print(f'{n}: {len(res)}/{len(src)} 条（有同义 {ns}、有反义 {na}），错误 {len(errs)}，缺 {len(miss)}')
elif cmd == 'review-make':
    size = arg('--size', 2500)
    done = set()
    for p in D.glob('R*.in.txt'):
        done |= set(inputs(p.name[:5]))
    L = []
    for n in names('S'):
        src, res, errs = read(n, 'out')
        if res is None or errs or len(res) != len(src):
            sys.exit(f'{n} 还没通过 check')
        L += [f"{k} | {f[1]} | {f[2]} | {f[4]} | {f[5]} | {', '.join(res[k][0]) or '-'} | {', '.join(res[k][1]) or '-'}"
              for k, f in src.items() if k not in done]
    if not L:
        sys.exit('没有新的审核条目')
    start = len(list(D.glob('R*.in.txt')))
    for i in range(0, len(L), size):
        (D / f'R{start + i // size + 1:04d}.in.txt').write_text('\n'.join(L[i:i + size]) + '\n', encoding='utf-8')
    print(f'新条目 {len(L)} 条 → {(len(L) - 1) // size + 1} 块，从 R{start + 1:04d} 起')
elif cmd in ('review-check', 'apply'):
    allsrc = {}
    for n in names('S'):
        allsrc.update(inputs(n))
    fixes, bad = {}, 0
    for n in names('R'):
        o = D / f'{n}.reviewer.txt'
        if not o.exists():
            print(f'{n}: 未完成'); bad += 1; continue
        rin = set(inputs(n))
        k = 0
        for i, l in enumerate(open(o, encoding='utf-8'), 1):
            if not l.strip():
                continue
            f = [x.strip() for x in l.split(' | ')]
            if len(f) == 7:
                l = ' | '.join([f[0], f[5], f[6]])  # 整行抄回来的
            try:
                if f[0] not in rin:
                    raise ValueError('sense_id 不在审核块里')
                sid, syn, ant = parse(l, allsrc)
                fixes[sid] = (syn, ant); k += 1
            except ValueError as e:
                bad += 1
                print(f'✗ {o.name} 第 {i} 行 {e}：{l.strip()[:70]}')
        print(f'{n}: 改 {k} 条')
    if cmd == 'apply':
        if bad:
            sys.exit('审核还有问题，先修')
        # 代词、限定词不收人称/物主/指示词当反义词（he→she、his→her、this→that 不算反义）；数量词（all→none）保留
        PRON = set('i me my mine we us our ours you your yours he him his she her hers it its they them their theirs '
                   'this that these those a an the'.split())
        out, n_drop = [], 0
        for n in names('S'):
            src, res, errs = read(n, 'out')
            for sid in src:
                syn, ant = fixes.get(sid, res[sid])
                if src[sid][2] in ('pron.', 'det.', 'aux.') and any(a.lower() in PRON for a in ant):
                    ant = [a for a in ant if a.lower() not in PRON]; n_drop += 1
                out.append({'sense_id': sid, 'synonyms': syn, 'antonyms': ant, 'revised': sid in fixes})
        with open(M / 'thesaurus.jsonl', 'w', encoding='utf-8', newline='\n') as f:
            for r in out:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        print(f'work/merged/thesaurus.jsonl {len(out)} 条（有同义 {sum(1 for r in out if r["synonyms"])}，有反义 {sum(1 for r in out if r["antonyms"])}，审核改 {len(fixes)}，代词反义规则去掉 {n_drop}）')
