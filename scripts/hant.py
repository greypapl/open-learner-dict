"""繁体中文（台湾用词）：OpenCC s2twp 全量转换 + 模型按上下文校对台湾用词。

  python -X utf8 -I scripts/hant.py make [--core-top 30000] [--size 2500]   # 读 release/<ver>/jsonl → work/hant/T*.in.txt、N*.in.txt
  python -X utf8 -I scripts/hant.py check
  python -X utf8 -I scripts/hant.py apply                                   # → data/hant-overrides.jsonl（release.py 读取）

T 块（释义）：`key | 英文 | 词性 | OpenCC 转出的繁体`      模型只输出要改的行：`key | 改后的繁体`
   key = 主词典 / 短语的 sense_id，或搭配的 id
N 块（专名）：`key | Display | 类型 | OpenCC 转出的中文名`   模型只输出要改的行：`key | 台湾通行译名`
   key = <专名 id>#<第几个名字>
没进 T 块的（主词典 3 万名以后、简释层）只有 OpenCC 结果。prompt: prompts/hant.md
"""
import json, re, sys
from pathlib import Path
from opencc import OpenCC

ROOT = Path(__file__).resolve().parent.parent
X = ROOT / 'work/hant'
VER = sys.argv[sys.argv.index('--version') + 1] if '--version' in sys.argv else '0.9.1'
REL = ROOT / 'release' / VER / 'jsonl'
CJK = re.compile(r'^[㐀-鿿豈-﫿，, …·\-—0-9%]+$')


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def load(name):
    return [json.loads(l) for l in open(REL / name, encoding='utf-8')]


def chunks(prefix, lines, size):
    for old in X.glob(f'{prefix}*.in.txt'):
        old.unlink()
    for i in range(0, len(lines), size):
        (X / f'{prefix}{i // size + 1:02d}.in.txt').write_text('\n'.join(lines[i:i + size]) + '\n', encoding='utf-8')
    return (len(lines) - 1) // size + 1


base = {}  # 进过校对块的全部 key → 校对员看到的文本（OpenCC s2twp 结果）


def read(prefix):
    res, errs, pend = {}, [], []
    for p in sorted(X.glob(f'{prefix}*.in.txt')):
        src = {}
        for l in open(p, encoding='utf-8'):
            f = l.rstrip('\n').split(' | ')
            if len(f) == 4:
                src[f[0]] = f[3]
        o = p.with_name(p.name.replace('.in.', '.out.'))
        if not o.exists():
            pend.append(p.name[:3]); continue
        for i, l in enumerate(open(o, encoding='utf-8'), 1):
            l = l.strip()
            if not l:
                continue
            f = [x.strip() for x in l.split(' | ')]
            if len(f) == 4 and f[0] in src:
                f = [f[0], f[3]]  # 有的 agent 把整行都抄回来了：取最后一栏
            if len(f) != 2 or f[0] not in src:
                errs.append(f'{o.name} 第 {i} 行格式错或 key 不在输入中：{l[:50]}'); continue
            if not CJK.match(f[1]):
                errs.append(f'{o.name} 第 {i} 行含非中文字符：{l[:50]}'); continue
            if prefix == 'T' and f[1].count(',') != src[f[0]].count(','):
                errs.append(f'{o.name} 第 {i} 行近义表达的个数变了：{l[:50]}'); continue
            if re.search(r'[A-Za-z\u0370-\u03ff]', src[f[0]]):
                continue  # 原文带字母（CT、PDF、γ）：校验不许输出字母，模型只能改写，这种改写不要
            if f[1] != src[f[0]]:
                res[f[0]] = f[1]
        base.update(src)
    return res, errs, pend


cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
if cmd == 'make':
    cc = OpenCC('s2twp')
    X.mkdir(parents=True, exist_ok=True)
    top = arg('--core-top', 30000)
    T = []
    for r in load('core.jsonl'):
        if r['rank'] <= top:
            T += [f"{s['sense_id']} | {r['word']} | {s['pos']} | {cc.convert(s['zh'])}" for s in r['senses']]
    for r in load('phrases.jsonl'):
        T += [f"{s['sense_id']} | {r['phrase']} | {s['pos']} | {cc.convert(s['zh'])}" for s in r['senses']]
    for r in load('collocations.jsonl'):
        T.append(f"{r['id']} | {r['collocation']} | {r['pattern']} | {cc.convert(r['zh'])}")
    N = [f"{r['id']}#{i} | {r['display']} | {n['type']}" + (f"（{cc.convert(n['note'])}）" if n['note'] else '') + f" | {cc.convert(n['zh'])}"
         for r in load('proper.jsonl') for i, n in enumerate(r['names'], 1)]
    size = arg('--size', 2500)
    print('T', len(T), '→', chunks('T', T, size), '块；N', len(N), '→', chunks('N', N, size), '块')
elif cmd == 'check':
    for k in 'TN':
        res, errs, pend = read(k)
        for e in errs[:15]:
            print('✗', e)
        print(f'{k}: 改 {len(res)} 行，格式问题 {len(errs)}，未完成 {" ".join(pend) or "无"}')
elif cmd == 'apply':
    out = {}
    for k in 'TN':
        res, errs, pend = read(k)
        if pend:
            sys.exit(f'{k} 未完成：{" ".join(pend)}')
        out.update(res)  # 有格式问题的行直接丢弃（保留校对员看到的文本）
    n_changed = len(out)
    BADTOK = ('型別', '釋出', '影象', '想象', '報道', '迴圈', '擴充套件', '全域性', '結束通話', '位元犬', '引數', '正規化', '衚衕', '賬')
    n_back = 0
    for k, v in base.items():  # 校对后没改的也写进去：这些 key 的繁体以校对员看过的为准
        if k in out:
            continue
        items = [x.strip() for x in v.split(',')]
        if len(set(items)) < len(items) or any(t in v for t in BADTOK):
            n_back += 1   # 校对员漏掉的 s2twp 误伤（重复项、已知错词）：不写覆盖，发布时退回 s2tw + 用词表
            continue
        out[k] = v
    print(f'残留误伤退回安全转换 {n_back} 条')
    (ROOT / 'data').mkdir(exist_ok=True)
    with open(ROOT / 'data/hant-overrides.jsonl', 'w', encoding='utf-8', newline='\n') as f:
        for k in sorted(out):
            f.write(json.dumps({'key': k, 'zh_hant': out[k]}, ensure_ascii=False) + '\n')
    print(f'data/hant-overrides.jsonl {len(out)} 条（其中模型改了 {n_changed} 条）')
