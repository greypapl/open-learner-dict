"""v0.9.0 抽检发现的 4 类系统性问题的定向修正。模型只输出需要改的行。

  python -X utf8 -I scripts/fixes.py make [--family-top 30000]   # 读 release/0.9.0/jsonl → work/fixes/*.in.txt
  python -X utf8 -I scripts/fixes.py check                       # 校验 work/fixes/*.out.txt
  python -X utf8 -I scripts/fixes.py apply                       # 写回 collocations.jsonl、phrases.jsonl，生成 work/merged/core-fixes.jsonl

四类（prompt 都在 prompts/fixes.md）：
  H  非标准词头      输入 `word | 首义项`              输出 `word | standard:<标准写法>`
  Y  短语写法        输入 `phrase | type`              输出 `phrase | fix:<正确写法>` 或 `phrase | solid:<应连写或加连字符的单词>`
  C  搭配分类        输入 `collocation | pattern`      输出 `collocation | <新 pattern>`
  F  词族            输入 `word: a, b, c`              输出 `word: <改后的列表或 ->`
core-fixes.jsonl 由 release.py 读取：{"id", "word"?（仅大小写改正）, "standard_form"?, "word_family"?}
"""
import csv, json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REL, M, X = ROOT / 'release/0.9.0/jsonl', ROOT / 'work/merged', ROOT / 'work/fixes'
PATTERNS = {'v+n', 'adj+n', 'n+n', 'adv+adj', 'v+adv', 'v+prep', 'adj+prep', 'n+prep', 'n+v', 'adv+v'}
csv.field_size_limit(10 ** 8)


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def load(p):
    return [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]


def chunks(prefix, lines, size):
    for old in X.glob(f'{prefix}*.in.txt'):
        old.unlink()
    for i in range(0, len(lines), size):
        (X / f'{prefix}{i // size + 1:02d}.in.txt').write_text('\n'.join(lines[i:i + size]) + '\n', encoding='utf-8')
    return (len(lines) - 1) // size + 1


def key(line, sep):
    return line.split(sep)[0].strip()


def read_kind(prefix, sep=' | '):
    """→ {key: 右半边}，以及错误列表、未完成块"""
    res, errs, pend = {}, [], []
    for p in sorted(X.glob(f'{prefix}*.in.txt')):
        src = {key(l, sep) for l in open(p, encoding='utf-8') if l.strip()}
        o = p.with_name(p.name.replace('.in.', '.out.'))
        if not o.exists():
            pend.append(p.name[:3]); continue
        for i, l in enumerate(open(o, encoding='utf-8'), 1):
            l = l.strip()
            if not l:
                continue
            if sep not in l:
                errs.append(f'{o.name} 第 {i} 行缺分隔符：{l[:60]}'); continue
            k, v = l.split(sep, 1)
            k, v = k.strip(), v.strip()
            if k not in src:
                errs.append(f'{o.name} 第 {i} 行不在输入中：{k}'); continue
            e = None
            if prefix == 'H' and not re.fullmatch(r"standard:[A-Za-z][A-Za-z' .&/-]*", v):
                e = 'H 行应为 standard:<写法>'
            if prefix == 'Y' and not re.fullmatch(r"(fix|solid):[A-Za-z][A-Za-z' .,!?-]*", v):
                e = 'Y 行应为 fix:<写法> 或 solid:<单词>'
            if prefix == 'C' and v not in PATTERNS:
                e = f'pattern 非法：{v}'
            if prefix == 'F' and v != '-' and not all(re.fullmatch(r"[A-Za-z][A-Za-z' -]*", x.strip()) for x in v.split(',')):
                e = '词族列表格式错'
            if e:
                errs.append(f'{o.name} 第 {i} 行 {e}：{l[:60]}')
            else:
                res[k] = v
    return res, errs, pend


cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
if cmd == 'make':
    X.mkdir(parents=True, exist_ok=True)
    core = load(REL / 'core.jsonl')
    W = {r['word'] for r in core}
    phr = load(REL / 'phrases.jsonl')
    two = {r['phrase'].lower() for r in phr}
    for r in csv.DictReader(open(ROOT / 'sources/ecdict.csv', encoding='utf-8')):
        w = r['word']
        if w.count(' ') == 1 and w.islower():
            two.add(w)
    H = []
    for r in core:
        w = r['word']
        cand = '-' in w or any(s['pos'] == 'abbr.' for s in r['senses'])
        if not cand and w.isalpha() and len(w) >= 6:  # 可能应分写的连写词：拆开后是词库里的两个词，且分写形式在短语层或 ECDICT 里
            cand = any(w[:i] in W and w[i:] in W and f'{w[:i]} {w[i:]}' in two for i in range(3, len(w) - 2))
        if cand:
            H.append(f"{w} | {r['senses'][0]['pos']}{r['senses'][0]['zh']}")
    top = arg('--family-top', 30000)
    F = [f"{r['word']}: {', '.join(r['word_family'])}" for r in core if r['word_family'] and r['rank'] <= top]
    col = load(REL / 'collocations.jsonl')
    C = [f"{r['collocation']} | {r['pattern']}" for r in col if r['pattern'] in ('v+prep', 'n+n', 'v+adv')]
    Y = [f"{r['phrase']} | {r['type']}" for r in phr]
    print('H', len(H), '→', chunks('H', H, 1700), '块；Y', len(Y), '→', chunks('Y', Y, 3400), '块；C', len(C), '→', chunks('C', C, 1700),
          '块；F', len(F), '→', chunks('F', F, 3500), '块')
elif cmd == 'check':
    for k, sep in (('H', ' | '), ('Y', ' | '), ('C', ' | '), ('F', ': ')):
        res, errs, pend = read_kind(k, sep)
        for e in errs[:15]:
            print('✗', e)
        print(f'{k}: 改 {len(res)} 行，格式问题 {len(errs)}，未完成 {" ".join(pend) or "无"}')
elif cmd == 'apply':
    out = {}
    for k, sep in (('H', ' | '), ('Y', ' | '), ('C', ' | '), ('F', ': ')):
        res, errs, pend = read_kind(k, sep)
        if errs or pend:
            sys.exit(f'{k} 未完成或有格式问题，先跑 check')
        out[k] = res
    core = {r['word']: r for r in load(REL / 'core.jsonl')}
    fixes = {}
    for w, v in out['H'].items():
        std = v[9:].strip()
        if std == w:
            continue
        f = fixes.setdefault(core[w]['id'], {'id': core[w]['id']})
        if std.lower() == w.lower():
            f['word'] = std               # 只差大小写：直接改词头（ngo → NGO）
        else:
            f['standard_form'] = std      # 写法不同：保留词条，标出标准写法（living-room → living room）
    nfam = 0
    for w, v in out['F'].items():
        new = [] if v == '-' else [x.strip() for x in v.split(',') if x.strip()]
        if new != core[w]['word_family'] and set(new) <= set(core[w]['word_family']):  # 只允许删，不允许加
            fixes.setdefault(core[w]['id'], {'id': core[w]['id']})['word_family'] = new
            nfam += 1
    with open(M / 'core-fixes.jsonl', 'w', encoding='utf-8') as fo:
        for f in fixes.values():
            fo.write(json.dumps(f, ensure_ascii=False) + '\n')
    # 搭配 pattern
    col = load(M / 'collocations.jsonl')
    nc = 0
    for r in col:
        p = out['C'].get(r['collocation'])
        if p and p != r['pattern']:
            r['pattern'] = p; nc += 1
    with open(M / 'collocations.jsonl', 'w', encoding='utf-8') as fo:
        for r in col:
            fo.write(json.dumps(r, ensure_ascii=False) + '\n')
    # 短语写法
    phr = load(M / 'phrases.jsonl')
    have = {r['phrase'].lower() for r in phr}
    keep, ny, ns, nd = [], 0, 0, 0
    with open(M / 'phrase-solid.jsonl', 'w', encoding='utf-8') as fs:
        for r in phr:
            v = out['Y'].get(r['phrase'])
            if v and v.startswith('solid:'):
                fs.write(json.dumps(dict(r, solid_form=v[6:].strip()), ensure_ascii=False) + '\n'); ns += 1
                continue
            if v:
                new = v[4:].strip()
                if new.lower() != r['phrase'].lower() and new.lower() in have:
                    nd += 1; continue      # 改正后与已有短语重复，去掉这条
                if new != r['phrase']:
                    have.add(new.lower()); r['phrase'] = new; ny += 1
            keep.append(r)
    with open(M / 'phrases.jsonl', 'w', encoding='utf-8') as fo:
        for r in keep:
            fo.write(json.dumps(r, ensure_ascii=False) + '\n')
    c = Counter('rename' if 'word' in f else 'standard_form' if 'standard_form' in f else 'family' for f in fixes.values())
    print(f'core-fixes.jsonl {len(fixes)} 条（{dict(c)}；词族改 {nfam}）；搭配 pattern 改 {nc}；'
          f'短语改写 {ny}、移出（应连写）{ns}、改后重复去掉 {nd}，剩 {len(keep)}')
