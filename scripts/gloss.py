"""简释扩展层（gloss-v1）：给初筛去掉的 too-rare 词写一行中文简释，单独成层，统一 confidence=low，不经审核。

  python -X utf8 -I scripts/gloss.py make [--size 1000]   # triage-skips.jsonl → work/gloss/G0001.in.txt …
  python -X utf8 -I scripts/gloss.py check [G0001 …]      # 校验 G*.out.txt；不带参数则检查全部并汇总
  python -X utf8 -I scripts/gloss.py merge                # → work/merged/gloss.jsonl + gloss-skips.jsonl
  python -X utf8 -I scripts/gloss.py make-unknown [--size 1000]  # G 层的 skip:unknown → work/gloss/U0001.in.txt …（Opus 重试）
  merge 时 U*.out.txt 中写出的简释覆盖 G 层的 unknown，source 记为 gloss-v1-opus

prompt: prompts/gloss.md
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
G, M = ROOT / 'work/gloss', ROOT / 'work/merged'
POS = {'n.', 'v.', 'adj.', 'adv.', 'prep.', 'conj.', 'pron.', 'det.', 'int.', 'num.', 'abbr.'}
DOM = set('医学 解剖 药学 生物 植物 动物 化学 物理 数学 天文 地质 地理 气象 计算机 电子 机械 建筑 军事 航海 航空 法律 经济 '
          '金融 商业 政治 宗教 哲学 语言 文学 音乐 美术 体育 烹饪 农业 心理 教育 历史 摄影 纺织 印刷 矿业 统计 逻辑 神话'.split())
TAGS = {'formal', 'informal', 'slang', 'dated', 'literary', 'uk', 'us', 'offensive-mild', 'offensive-strong'}
SKIPS = {'junk', 'not-english', 'not-lemma', 'proper-out-of-scope', 'unknown'}
SENSE = re.compile(r'^(n\.|v\.|adj\.|adv\.|prep\.|conj\.|pron\.|det\.|int\.|num\.|abbr\.)(.+?)(?:\s*\[([^\]]+)\])?$')


def parse(line, word):
    f = [x.strip() for x in line.split(' | ')]
    if f[0] != word:
        raise ValueError(f'词头不符: {f[0]!r} ≠ {word!r}')
    if len(f) == 2 and f[1].startswith('skip:'):
        r = f[1][5:]
        if r not in SKIPS:
            raise ValueError(f'skip 原因非法: {r}')
        return {'skip': r}
    if len(f) not in (2, 3) or (len(f) == 3 and f[2] != 'nokid'):
        raise ValueError('字段数不对')
    senses = []
    parts = [p.strip() for p in f[1].split(' ; ')]
    if len(parts) > 2:
        raise ValueError('超过 2 个义项')
    for p in parts:
        m = SENSE.match(p)
        if not m:
            raise ValueError(f'义项格式错: {p}')
        zh = [z.strip() for z in m.group(2).split(',') if z.strip()]
        if not 1 <= len(zh) <= 3 or any(len(z) > 12 or re.search(r'[()（）；。;\[\]a-zA-Z]', z) for z in zh):
            raise ValueError(f'中文不合规: {m.group(2)}')
        tags = [t.strip() for t in (m.group(3) or '').split(',') if t.strip()]
        for t in tags:
            if t not in TAGS and not (t.startswith('domain:') and t[7:] in DOM):
                raise ValueError(f'标签非法: {t}')
        senses.append({'pos': m.group(1), 'zh': zh, 'tags': tags})
    return {'senses': senses, 'flags': ['nokid'] if len(f) == 3 else []}


def check(name):
    inp, out = G / f'{name}.in.txt', G / f'{name}.out.txt'
    words = [l.strip() for l in open(inp, encoding='utf-8') if l.strip()]
    if not out.exists():
        return None, ['missing']
    lines = [l.rstrip('\n') for l in open(out, encoding='utf-8') if l.strip()]
    errs = []
    if len(lines) != len(words):
        errs.append(f'行数 {len(lines)} ≠ 输入 {len(words)}')
    res = []
    for i, (w, l) in enumerate(zip(words, lines), 1):
        try:
            res.append(parse(l, w))
        except ValueError as e:
            errs.append(f'第 {i} 行 {w}: {e}')
    return res, errs


cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
if cmd == 'make':
    size = int(sys.argv[sys.argv.index('--size') + 1]) if '--size' in sys.argv else 1000
    G.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(l) for l in open(M / 'triage-skips.jsonl', encoding='utf-8') if l.strip()]
    for i in range(0, len(rows), size):
        (G / f'G{i // size + 1:04d}.in.txt').write_text('\n'.join(r['word'] for r in rows[i:i + size]) + '\n', encoding='utf-8')
    print(len(rows), 'words →', len(list(G.glob('G*.in.txt'))), 'chunks')
elif cmd == 'make-unknown':
    size = int(sys.argv[sys.argv.index('--size') + 1]) if '--size' in sys.argv else 1000
    words = [json.loads(l)['word'] for l in open(M / 'gloss-skips.jsonl', encoding='utf-8')
             if l.strip() and json.loads(l)['skip'] == 'unknown']
    for i in range(0, len(words), size):
        (G / f'U{i // size + 1:04d}.in.txt').write_text('\n'.join(words[i:i + size]) + '\n', encoding='utf-8')
    print(len(words), 'unknown words →', len(list(G.glob('U*.in.txt'))), 'chunks')
elif cmd == 'check':
    names = sys.argv[2:] or sorted(p.name[:5] for p in G.glob('G*.in.txt'))
    done = kept = skip = 0
    pend = []
    for n in names:
        res, errs = check(n)
        if errs == ['missing']:
            pend.append(n)
            continue
        if errs:
            print(f'✗ {n}: {len(errs)} 处问题'); [print('  ', e) for e in errs[:15]]
            continue
        done += 1
        k = sum(1 for r in res if 'senses' in r)
        kept += k; skip += len(res) - k
        if len(sys.argv) > 2:
            print(f'✓ {n}: {k} 条简释, {len(res) - k} 个 skip')
    print(f'通过 {done} 块：简释 {kept}，skip {skip}；未完成 {len(pend)} 块')
elif cmd == 'merge':
    rows = [json.loads(l) for l in open(M / 'triage-skips.jsonl', encoding='utf-8') if l.strip()]
    byword = {}
    for n in sorted(p.name[:5] for p in G.glob('G*.in.txt')):
        res, errs = check(n)
        if errs:
            sys.exit(f'{n} 未通过校验，先跑 check')
        words = [l.strip() for l in open(G / f'{n}.in.txt', encoding='utf-8') if l.strip()]
        byword.update((w, dict(r, source='gloss-v1')) for w, r in zip(words, res))
    for n in sorted(p.name[:5] for p in G.glob('U*.in.txt')):
        res, errs = check(n)
        if errs:
            print(f'跳过 {n}：{errs[0]}')
            continue
        words = [l.strip() for l in open(G / f'{n}.in.txt', encoding='utf-8') if l.strip()]
        for w, r in zip(words, res):
            if 'senses' in r and byword.get(w, {}).get('skip') == 'unknown':
                byword[w] = dict(r, source='gloss-v1-opus')
    k = s = 0
    with open(M / 'gloss.jsonl', 'w', encoding='utf-8') as fg, open(M / 'gloss-skips.jsonl', 'w', encoding='utf-8') as fs:
        for r in rows:
            g = byword[r['word']]
            if 'senses' in g:
                fg.write(json.dumps({'id': r['id'], 'word': r['word'], 'senses': g['senses'], 'flags': g['flags'],
                                     'confidence': 'low', 'layer': 'gloss', 'source': g['source']}, ensure_ascii=False) + '\n')
                k += 1
            else:
                fs.write(json.dumps({'id': r['id'], 'word': r['word'], 'skip': g['skip'], 'by': 'gloss-v1'}, ensure_ascii=False) + '\n')
                s += 1
    print(f'gloss.jsonl {k} 条，gloss-skips.jsonl {s} 个')
