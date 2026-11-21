"""变形索引：屈折形式 → 原词（went→go、children→child、best→good）。纯脚本，不用模型。

  python -X utf8 -I scripts/inflect.py      # → work/merged/inflections.jsonl

来源（可信度从高到低）：
  main    主词典词条的 inflections 字段
  ecdict  ECDICT exchange 字段（原词行的 p/d/i/3/r/t/s，以及变形行的 0:原词/1:类型）
          ECDICT 有噪声（如 childrens），所以 ecdict 来源的形式要求 wordfreq zipf ≥ 1.5，或已被 main 证实
只收原词在主词典或简释层里的；形式本身也是词头的（left、saw）照收，并标 headword=true。
not-lemma skip 记录用来统计覆盖率（没被解析的会打印出来）。

输出每行一个形式：{"form", "lemmas":[{"lemma","types":[…],"src":[…]}], "headword": bool}
"""
import csv, glob, json, sys
from collections import defaultdict
from pathlib import Path
from wordfreq import zipf_frequency

ROOT = Path(__file__).resolve().parent.parent
M = ROOT / 'work/merged'
CODE = {'p': 'past', 'd': 'past_participle', 'i': 'present_participle', '3': 'third_person',
        'r': 'comparative', 't': 'superlative', 's': 'plural'}
csv.field_size_limit(10 ** 8)

entries = {}
for f in sorted(glob.glob(str(M / 'B[0-9][0-9][0-9][0-9].jsonl'))):
    for l in open(f, encoding='utf-8'):
        r = json.loads(l)
        entries[r['word']] = r.get('inflections') or {}
gloss = {json.loads(l)['word'] for l in open(M / 'gloss.jsonl', encoding='utf-8') if l.strip()}
lemmas = set(entries) | gloss

pairs = defaultdict(lambda: defaultdict(lambda: [set(), set()]))  # form → lemma → [types, srcs]


def add(form, lemma, typ, src):
    form, lemma = form.strip(), lemma.strip()
    if not form or not lemma or form == lemma or ' ' in form or lemma not in lemmas:
        return
    t = pairs[form][lemma]
    t[0].add(typ); t[1].add(src)


for w, inf in entries.items():
    for typ, v in inf.items():
        if isinstance(v, str):
            add(v, w, typ, 'main')

for row in csv.DictReader(open(ROOT / 'sources/ecdict.csv', encoding='utf-8')):
    ex = row.get('exchange') or ''
    if not ex:
        continue
    kv = dict(p.split(':', 1) for p in ex.split('/') if ':' in p)
    w = row['word']
    if w in lemmas:
        for c, typ in CODE.items():
            for form in kv.get(c, '').split(','):
                if form:
                    add(form, w, typ, 'ecdict')
    if '0' in kv:
        typs = [CODE[c] for c in kv.get('1', '') if c in CODE] or ['form']
        for typ in typs:
            add(w, kv['0'], typ, 'ecdict')

# not-lemma skip 是模型确认过的屈折形式：用手工表 + 去后缀规则补上 ECDICT 没有的（are、gotten、canceled、thousands）
MANUAL = {'are': ('be', 'present'), 'were': ('be', 'past'), 'am': ('be', 'present'), 'gotten': ('get', 'past_participle'),
          'hath': ('have', 'third_person'), 'hast': ('have', 'present'), 'doth': ('do', 'third_person'),
          'dost': ('do', 'present'), 'didst': ('do', 'past'), 'saith': ('say', 'third_person'),
          'shalt': ('shall', 'present'), 'canst': ('can', 'present'), 'durst': ('dare', 'past'),
          'begat': ('beget', 'past'), 'strewn': ('strew', 'past_participle'), 'misspoke': ('misspeak', 'past'),
          'farthest': ('far', 'superlative'), 'fewest': ('few', 'superlative'), 'automata': ('automaton', 'plural'),
          'quanta': ('quantum', 'plural'), 'lire': ('lira', 'plural'), 'wouldest': ('would', 'archaic'),
          'couldest': ('could', 'archaic'), 'wouldst': ('would', 'archaic'), 'shouldst': ('should', 'archaic'),
          'hadst': ('have', 'archaic'), 'wist': ('wit', 'past'), 'relit': ('relight', 'past'), 'alit': ('alight', 'past'),
          'eave': ('eaves', 'singular')}


def guesses(w):
    if w.endswith('ies'): yield w[:-3] + 'y', 'plural'
    if w.endswith('es'): yield w[:-2], 'plural'
    if w.endswith('s'): yield w[:-1], 'plural'
    if w.endswith('men'): yield w[:-3] + 'man', 'plural'
    if w.endswith('people'): yield w[:-6] + 'person', 'plural'
    if w.endswith('children'): yield w[:-8] + 'child', 'plural'
    for a, b in (('ae', 'a'), ('ata', 'a'), ('ina', 'en'), ('ia', 'ium'), ('ia', 'ion'), ('a', 'um'), ('a', 'on'),
                 ('i', 'us'), ('ra', 'r'), ('ra', 'rum'), ('era', 'us'), ('ges', 'x')):
        if w.endswith(a): yield w[:-len(a)] + b, 'plural'
    for suf, typ in (('ed', 'past'), ('ing', 'present_participle'), ('er', 'comparative'), ('est', 'superlative')):
        if w.endswith(suf):
            b = w[:-len(suf)]
            yield b, typ
            yield b + 'e', typ
            if len(b) > 2 and b[-1] == b[-2]: yield b[:-1], typ
            if b.endswith('i'): yield b[:-1] + 'y', typ
            if typ == 'past' and b.endswith('el'): yield b, typ  # canceled ← cancel


skips_nl = [json.loads(l)['word'] for p in glob.glob(str(M / 'B*.skips.jsonl')) for l in open(p, encoding='utf-8')
            if l.strip() and json.loads(l)['skip'] == 'not-lemma']
for w in skips_nl:
    if w in pairs:
        continue
    if w in MANUAL:
        add(w, *MANUAL[w][:1], MANUAL[w][1], 'manual')
        continue
    for b, typ in guesses(w):
        if b in lemmas:
            add(w, b, typ, 'rule')  # -s 形式一律记 plural（与 third_person 不区分）
            break

out, dropped = [], 0
for form in sorted(pairs):
    ls = []
    for lemma, (typs, srcs) in sorted(pairs[form].items()):
        if srcs == {'ecdict'} and zipf_frequency(form, 'en') < 1.5:
            dropped += 1
            continue
        ls.append({'lemma': lemma, 'types': sorted(typs), 'src': sorted(srcs)})
    if ls:
        out.append({'form': form, 'lemmas': ls, 'headword': form in lemmas})

with open(M / 'inflections.jsonl', 'w', encoding='utf-8') as f:
    for r in out:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')

forms = {r['form'] for r in out}
nl = [json.loads(l)['word'] for p in glob.glob(str(M / 'B*.skips.jsonl')) for l in open(p, encoding='utf-8')
      if l.strip() and json.loads(l)['skip'] == 'not-lemma']
miss = [w for w in nl if w not in forms]
print(f'inflections.jsonl {len(out)} 个形式（其中 {sum(r["headword"] for r in out)} 个本身也是词头），'
      f'ecdict 低频噪声丢弃 {dropped} 对')
print(f'not-lemma skip {len(nl)} 个，已覆盖 {len(nl) - len(miss)}，未覆盖 {len(miss)}：{" ".join(miss[:60])}')
