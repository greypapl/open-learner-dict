"""专名层审核（proper-review-v1）：Opus 逐个名字看中文译名、类型、说明，只输出要改的行。

  python -X utf8 -I scripts/proper_review.py make [--version 0.10.0] [--size 1500]   # 发布包 proper.jsonl → work/proper-review/P01.in.txt
  python -X utf8 -I scripts/proper_review.py check [P01 …]
  python -X utf8 -I scripts/proper_review.py apply                                    # → work/merged/proper-review.jsonl（release.py 读取）

输入行（每个名字一行，同一词条的名字相邻）：<p_id>#<i> | Display | type | 中文名 | 说明 | 台湾译名
输出（只写要改的）：
  <p_id>#<i> | type | 中文名 | 说明 | 台湾译名     改这个名字；i = 现有个数 + 1 表示新增一个名字（每个词条最多 3 个）
  <p_id>#<i> | drop | 原因                          去掉这个名字（词条至少留一个）
  <p_id> | display | 新写法                         改显示写法（只改大小写、标点、撇号，如 McDonald's、J.D.）
  <p_id> | delete | 原因                            删整个词条（不是专名、拼写错误、无意义的复数形式）
prompt: prompts/proper-review.md
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RND = sys.argv[sys.argv.index('--round') + 1] if '--round' in sys.argv else ''  # 第二轮：--round 2 → work/proper-review2、proper-review2.jsonl
D, M = ROOT / f'work/proper-review{RND}', ROOT / 'work/merged'
TYPES = {'person', 'place', 'brand', 'org', 'abbr', 'work', 'people', 'religion', 'event', 'other'}
BAD = re.compile(r'[()（）；;。\[\]|]')


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def names():
    sel = [a for a in sys.argv[2:] if re.fullmatch(r'P\d{2}', a)]
    return sel or sorted(p.name[:3] for p in D.glob('P*.in.txt'))


def norm(x):
    return re.sub(r"[\s.'’!\-]", '', x.lower())


def ok_name(z):
    return 1 <= len(z) <= 16 and not BAD.search(z)


def read(n):
    src, cnt, disp = {}, {}, {}
    for l in open(D / f'{n}.in.txt', encoding='utf-8'):
        f = l.rstrip('\n').split(' | ')
        src[f[0]] = f
        pid = f[0].split('#')[0]
        cnt[pid] = cnt.get(pid, 0) + 1; disp[pid] = f[1]
    o = D / f'{n}.reviewer.txt'
    if not o.exists():
        return None, src, []
    ed, errs = {'name': {}, 'drop': {}, 'display': {}, 'delete': {}}, []
    for i, l in enumerate(open(o, encoding='utf-8'), 1):
        if not l.strip():
            continue
        f = [x.strip() for x in l.split(' | ')]
        e = lambda m: errs.append(f'{o.name} 第 {i} 行 {m}：{l.strip()[:70]}')
        k = f[0]
        if '#' not in k:
            if k not in cnt:
                e('词条 id 不在输入中'); continue
            if len(f) == 3 and f[1] == 'delete':
                ed['delete'][k] = f[2]; continue
            if len(f) == 3 and f[1] == 'display':
                if norm(f[2]) != norm(disp[k]):
                    e('display 只能改大小写、标点、撇号、空格'); continue
                ed['display'][k] = f[2]; continue
            e('格式错'); continue
        pid, _, idx = k.partition('#')
        if pid not in cnt or not idx.isdigit() or not 1 <= int(idx) <= cnt[pid] + 1:
            e('key 不在输入中（新增名字只能用 现有个数+1）'); continue
        if len(f) == 3 and f[1] == 'drop':
            if k not in src:
                e('要去掉的名字不存在'); continue
            ed['drop'][k] = f[2]; continue
        if len(f) == 6 and k in src:  # 整行抄回来的（带 Display）
            f = [f[0]] + f[2:]
        if len(f) != 5:
            e(f'字段数 {len(f)} ≠ 5'); continue
        if f[1] not in TYPES:
            e(f'type 非法：{f[1]}'); continue
        if not ok_name(f[2]) or not ok_name(f[4]) or len(f[3]) > 20 or BAD.search(f[3]):
            e('中文名/台湾名 1–16 字、说明 ≤20 字，都不带括号和；。|'); continue
        if k in src and f[1:] == src[k][2:]:
            continue  # 没改
        ed['name'][k] = {'type': f[1], 'zh': f[2], 'note': f[3], 'zh_hant': f[4]}
    for pid in {k.split('#')[0] for k in ed['drop']}:
        left = cnt[pid] - sum(1 for k in ed['drop'] if k.split('#')[0] == pid) + sum(1 for k in ed['name'] if k.split('#')[0] == pid and k not in src)
        if left < 1 and pid not in ed['delete']:
            errs.append(f'{pid} 名字全去掉了（要删整个词条就用 delete）')
    return ed, src, errs


cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
if cmd == 'make':
    D.mkdir(parents=True, exist_ok=True)
    ver, size = arg('--version', '0.10.0'), arg('--size', 1500)
    if list(D.glob('P*.in.txt')):
        sys.exit(f'已经切过块了；要重切先删掉 {D}/P*.in.txt')
    chunks, cur = [], []
    for r in (json.loads(l) for l in open(ROOT / 'release' / ver / 'jsonl/proper.jsonl', encoding='utf-8')):
        if len(cur) >= size:
            chunks.append(cur); cur = []
        cur += [f"{r['id']}#{i} | {r['display']} | {n['type']} | {n['zh']} | {n['note'] or '-'} | {n['zh_hant']}" for i, n in enumerate(r['names'], 1)]
    chunks.append(cur)
    for j, c in enumerate(chunks, 1):
        (D / f'P{j:02d}.in.txt').write_text('\n'.join(c) + '\n', encoding='utf-8')
    print(f'{sum(map(len, chunks))} 个名字 → {len(chunks)} 块')
elif cmd in ('check', 'apply'):
    allr = {'name': {}, 'drop': {}, 'display': {}, 'delete': {}}
    pend, bad, reviewed = [], 0, set()
    for n in names():
        ed, src, errs = read(n)
        if ed is None:
            pend.append(n); continue
        reviewed |= {k.split('#')[0] for k in src}
        for e in errs[:15]:
            print('✗', e)
        bad += len(errs)
        zh = sum(1 for k, v in ed['name'].items() if k not in src or v['zh'] != src[k][3])
        print(f'{n}: 改名字 {len(ed["name"])}（译名变 {zh}），去名字 {len(ed["drop"])}，改写法 {len(ed["display"])}，删词条 {len(ed["delete"])}，格式问题 {len(errs)}')
        for t in allr:
            allr[t].update(ed[t])
    print(f'合计 ' + '，'.join(f'{t} {len(v)}' for t, v in allr.items()) + f'；未完成 {" ".join(pend) or "无"}')
    if cmd == 'apply':
        if pend or bad:
            sys.exit('还有未完成或格式问题')
        with open(M / f'proper-review{RND}.jsonl', 'w', encoding='utf-8', newline='\n') as f:
            for k, v in sorted(allr['name'].items()):
                f.write(json.dumps({'key': k, **v}, ensure_ascii=False) + '\n')
            for t in ('drop', 'display', 'delete'):
                for k, v in sorted(allr[t].items()):
                    f.write(json.dumps({t: k, 'value': v}, ensure_ascii=False) + '\n')
            f.write(json.dumps({'reviewed_ids': sorted(reviewed)}, ensure_ascii=False) + '\n')
        print(f'work/merged/proper-review{RND}.jsonl 已写，审过 {len(reviewed)} 个词条')
