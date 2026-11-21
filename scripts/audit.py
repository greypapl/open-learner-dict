"""质量抽检：从发布版分层抽样，交给独立模型（Fable）逐条判断，再统计错误率。

  python -X utf8 -I scripts/audit.py sample [--version 0.10.0] [--seed 20261121] [--n 300]   # → work/audit-<ver>/A01.in.txt …
  python -X utf8 -I scripts/audit.py check [--version 0.10.0]                                 # 校验 A*.out.txt
  python -X utf8 -I scripts/audit.py report [--version 0.10.0]                                # → reports/quality-<ver>.md + findings.jsonl

v0.9.0（work/audit，prompts/audit.md 的 v1 口径）：主词典 5 段各 100、简释/专名/短语/搭配各 100，共 900 条。
v0.10.0 起（audit-v2，更严）：每层 n 条（主词典 5 段各 n/5），另加例句层和繁体层（审过的释义 / 没审的释义 / 例句译文各 n/3）。
prompt: prompts/audit.md        判定行：`id | ok` 或 `id | major|minor | 类别 | 说明`
"""
import json, random, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


VER = arg('--version', '0.10.0')
A = ROOT / ('work/audit' if VER == '0.9.0' else f'work/audit-{VER}')
N = int(arg('--n', '300' if VER != '0.9.0' else '100'))
BANDS = [('core 1–2,000', 1, 2000), ('core 2,001–10,000', 2001, 10000), ('core 10,001–30,000', 10001, 30000),
         ('core 30,001–60,000', 30001, 60000), ('core 60,001+', 60001, 10 ** 9)]
CATS = {'meaning', 'order', 'missing', 'pos', 'ipa', 'level', 'zh', 'tag', 'form', 'not-entry', 'example', 'hant', 'other'}
HANT = ['zh_hant 已校对释义', 'zh_hant 未校对释义', 'zh_hant 例句译文']
ORDER = [b[0] for b in BANDS] + ['gloss', 'proper', 'phrase', 'collocation', 'example'] + HANT


def load(name):
    return [json.loads(l) for l in open(ROOT / 'release' / VER / 'jsonl' / name, encoding='utf-8')]


def sense(s):
    t = f"{s['pos']}{s['zh']}" + (f" = {s['en_short']}" if s.get('en_short') else '')
    return t + (f" [{','.join(s['register'])}]" if s.get('register') else '')


def lines(rnd):
    out = []  # (stratum, id, line)
    core = load('core.jsonl')
    per = N // 5 if VER != '0.9.0' else N
    for name, lo, hi in BANDS:
        for r in rnd.sample([r for r in core if lo <= r['rank'] <= hi], per):
            out.append((name, r['id'], f"{r['id']} | {r['word']} | {' ; '.join(sense(s) for s in r['senses'])} | US {r['ipa_us']} | UK {r['ipa_uk']} | "
                                      f"{r['syllables']} | {r['level']} | family: {', '.join(r['word_family']) or '-'}"))
    gloss = load('gloss.jsonl')
    for r in rnd.sample(gloss, N):
        out.append(('gloss', r['id'], f"{r['id']} | {r['word']} | {' ; '.join(sense(s) for s in r['senses'])}"))
    for r in rnd.sample(load('proper.jsonl'), N):
        out.append(('proper', r['id'], f"{r['id']} | {r['display']} | " + ' ; '.join(f"{n['type']}:{n['zh']}" + (f"={n['note']}" if n['note'] else '') for n in r['names'])))
    for r in rnd.sample(load('phrases.jsonl'), N):
        out.append(('phrase', r['id'], f"{r['id']} | {r['phrase']} | {r['type']} | {' ; '.join(sense(s) for s in r['senses'])} | {r['level']}"))
    for r in rnd.sample(load('collocations.jsonl'), N):
        out.append(('collocation', r['id'], f"{r['id']} | {r['collocation']} | {r['pattern']} | {r['zh']}"))
    if VER == '0.9.0':
        return out
    # 例句：一个义项一条，给出该词的全部义项，便于判断例句体现的是不是这个义项
    ex = [(r, s) for r in core for s in r['senses'] if s['examples']]
    for r, s in rnd.sample(ex, N):
        e = s['examples'][0]
        others = ' ; '.join(f"{x['sense_id'].split('.')[1]}:{x['pos']}{x['zh']}" for x in r['senses'])
        out.append(('example', 'ex_' + s['sense_id'],
                    f"ex_{s['sense_id']} | {r['word']} | THIS SENSE {s['pos']}{s['zh']} = {s['en_short']} | all senses: {others} | {e['en']} | {e['zh']}"))
    # 繁体：简体 → 繁体（台湾用词）
    k = N // 3
    rev = [(r['word'], s) for r in core if r['rank'] <= 30000 for s in r['senses']]
    unrev = [(r['word'], s) for r in core if r['rank'] > 30000 for s in r['senses']] + [(r['word'], s) for r in gloss for s in r['senses']]
    for stratum, pool in ((HANT[0], rev), (HANT[1], unrev)):
        for w, s in rnd.sample(pool, k):
            out.append((stratum, 'hz_' + s['sense_id'], f"hz_{s['sense_id']} | {w} | 简体 {s['zh']} | 繁体 {s['zh_hant']}"))
    for r, s in rnd.sample(ex, k):
        e = s['examples'][0]
        out.append((HANT[2], 'hx_' + s['sense_id'], f"hx_{s['sense_id']} | {r['word']} | 简体 {e['zh']} | 繁体 {e['zh_hant']}"))
    return out


def read_out():
    idx = json.loads((A / 'index.json').read_text(encoding='utf-8'))
    res, errs, pend = {}, [], []
    for p in sorted(A.glob('A*.in.txt')):
        ids = [l.split(' | ')[0] for l in open(p, encoding='utf-8') if l.strip()]
        o = p.with_name(p.name.replace('.in.', '.out.'))
        if not o.exists():
            pend.append(p.name[:3]); continue
        got = {}
        for i, l in enumerate(open(o, encoding='utf-8'), 1):
            f = [x.strip() for x in l.strip().split(' | ')]
            if not l.strip():
                continue
            if f[0] not in ids:
                errs.append(f'{o.name} 第 {i} 行：id 不在输入中 {f[0]}'); continue
            if len(f) == 2 and f[1] == 'ok':
                got[f[0]] = None
            elif len(f) == 4 and f[1] in ('major', 'minor') and f[2] in CATS:
                got[f[0]] = {'severity': f[1], 'category': f[2], 'note': f[3]}
            else:
                errs.append(f'{o.name} 第 {i} 行格式错：{l.strip()[:80]}')
        miss = [x for x in ids if x not in got]
        if miss:
            errs.append(f'{o.name} 缺 {len(miss)} 条判定，如 {miss[:3]}')
        res.update(got)
    return idx, res, errs, pend


cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
if cmd == 'sample':
    rows = lines(random.Random(int(arg('--seed', '20261121'))))
    random.Random(1).shuffle(rows)  # 打乱层次，避免一个 agent 只看到同一层
    A.mkdir(parents=True, exist_ok=True)
    for old in A.glob('A*.in.txt'):
        old.unlink()
    (A / 'index.json').write_text(json.dumps({i: s for s, i, _ in rows}, ensure_ascii=False), encoding='utf-8')
    (A / 'lines.json').write_text(json.dumps({i: l for _, i, l in rows}, ensure_ascii=False), encoding='utf-8')
    for k in range(0, len(rows), 150):
        (A / f'A{k // 150 + 1:02d}.in.txt').write_text('\n'.join(l for _, _, l in rows[k:k + 150]) + '\n', encoding='utf-8')
    print(len(rows), 'items →', (len(rows) - 1) // 150 + 1, 'chunks in', A.relative_to(ROOT))
elif cmd == 'check':
    idx, res, errs, pend = read_out()
    for e in errs[:30]:
        print('✗', e)
    print(f'已判定 {len(res)} / {len(idx)}；格式问题 {len(errs)}；未完成 {" ".join(pend) or "无"}')
elif cmd == 'report':
    idx, res, errs, pend = read_out()
    if errs or pend:
        sys.exit('抽检未完成或有格式问题，先跑 check')
    text = json.loads((A / 'lines.json').read_text(encoding='utf-8'))
    tot, maj, mi, cat = Counter(), Counter(), Counter(), defaultdict(Counter)
    with open(A / 'findings.jsonl', 'w', encoding='utf-8') as f:
        for i, s in idx.items():
            tot[s] += 1
            r = res[i]
            if r:
                (maj if r['severity'] == 'major' else mi)[s] += 1
                cat[s][r['category']] += 1
                f.write(json.dumps(dict(r, id=i, stratum=s, line=text[i]), ensure_ascii=False) + '\n')
    strict = VER != '0.9.0'
    md = [f'# 质量抽检报告 · v{VER}', '',
          '由独立模型（Claude Fable）对发布版分层随机抽样逐条判断。抽样脚本 `scripts/audit.py`，判定规则 `prompts/audit.md`'
          + ('（audit-v2，比 v0.9.0 的口径更严）' if strict else '') + '，',
          f'全部问题条目见 `{(A / "findings.jsonl").relative_to(ROOT).as_posix()}`。**这是模型抽检，不是人工校对**；错误率是估计值，'
          + ('每层 300 条时 95% 置信区间约 ±2–3 个百分点（错误率 5% 左右时），主词典每段 60 条、繁体每段 100 条时约 ±4–5。' if strict else '每层 100 条时误差约 ±5 个百分点。'), '',
          '- **major**：会误导使用者（释义错' + ('，或列出的几个中文对应词里有一个是错的' if strict else '') + '、词性错、主要义项缺失或排序明显不对、不该收录'
          + ('、例句体现的不是该义项、繁体用错字或用了大陆说法' if strict else '') + '）。',
          '- **minor**：不影响理解但不够好（音标小错、级别偏差、中文不自然、标签不准）。', '',
          '| 层 | 抽样 | major | minor | major 率 | 有问题合计 | 主要问题类别 |', '|---|---|---|---|---|---|---|']
    for s in [x for x in ORDER if tot[x]]:
        n = tot[s]
        md.append(f'| {s} | {n} | {maj[s]} | {mi[s]} | {100 * maj[s] / n:.0f}% | {100 * (maj[s] + mi[s]) / n:.0f}% | '
                  + ('、'.join(f'{k} {v}' for k, v in cat[s].most_common(3)) or '—') + ' |')
    c5 = [b[0] for b in BANDS]
    nc = sum(tot[s] for s in c5)
    md += ['', f'主词典 {nc} 条合计：major {sum(maj[s] for s in c5)}（{100 * sum(maj[s] for s in c5) / nc:.1f}%），'
               f'minor {sum(mi[s] for s in c5)}（{100 * sum(mi[s] for s in c5) / nc:.1f}%）。', '']
    notes = ROOT / 'reports' / f'quality-{VER}.notes.md'  # 维护者手写的解读，附在统计表后面
    if notes.exists():
        md += [notes.read_text(encoding='utf-8').rstrip()]
    (ROOT / 'reports' / f'quality-{VER}.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md[8:]))
