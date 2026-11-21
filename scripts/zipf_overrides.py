"""主词典词频修正表：和人名、品牌、动词变形同形的词，wordfreq 频率虚高（john 排第 342）。

  python -X utf8 -I scripts/zipf_overrides.py [--gap 1.5]   # → data/zipf-overrides.tsv

两部分：
- coca：级别 C1/C2、zipf ≥ 3，且 ECDICT 的 COCA 词频名次（frq，按普通词用法统计）推出的 zipf 比 wordfreq 低 gap 以上。
  替换成 COCA 推出的值。例：john 5.38 → 2.99，trying（形容词 难受的）5.47 → 2.95。
- manual：COCA 没有数据、但明显是人名/姓氏同形的词（下面 MANUAL），替换成同级别单词 zipf 的中位数。
release.py 读这个表，zipf_source 标成 coca-estimate / level-estimate。表是生成后人工看过的，可以手改。
"""
import bisect, csv, json, math, statistics, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAP = float(sys.argv[sys.argv.index('--gap') + 1]) if '--gap' in sys.argv else 1.5
MANUAL = '''smith lee warren ken turner cole brad bailey ruth hart troy cox heather kirk fletcher tucker wheeler chandler
holt tanner mercer dirk clement felicity wally willy lister prentice grange angelica joss shea newton roger romeo
cinderella sierra raj rand hale pip xi mason fisher don lance'''.split()

E = {}
for r in csv.DictReader(open(ROOT / 'sources/ecdict.csv', encoding='utf-8')):
    E.setdefault(r['word'].lower(), int(r['frq'] or 0))
import glob
from wordfreq import tokenize
rows = [json.loads(l) for f in sorted(glob.glob(str(ROOT / 'work/merged/B[0-9][0-9][0-9][0-9].jsonl'))) for l in open(f, encoding='utf-8') if l.strip()]
# 读原始批次（wordfreq 原值），不读发布包：发布包里已经应用了本表，重新生成会漏掉已修正的词
src = lambda r: 'multi' if len(tokenize(r['word'], 'en')) > 1 else 'wordfreq'
bins = defaultdict(list)  # frq 名次 → zipf：用普通单词拟合（log2 名次每半格取中位数，线性插值）
for r in rows:
    f = E.get(r['word'].lower(), 0)
    if f and src(r) == 'wordfreq' and r['zipf']:
        bins[round(math.log2(f) * 2) / 2].append(r['zipf'])
xs = sorted(bins); ys = [statistics.median(bins[x]) for x in xs]


def pred(f):
    x = math.log2(f); i = bisect.bisect_left(xs, x)
    if i <= 0: return ys[0]
    if i >= len(xs): return ys[-1]
    t = (x - xs[i - 1]) / (xs[i] - xs[i - 1]); return ys[i - 1] + t * (ys[i] - ys[i - 1])


lv = defaultdict(list)
for r in rows:
    if src(r) == 'wordfreq' and r['zipf']:
        lv[r['level']].append(r['zipf'])
LEVEL_ZIPF = {k: sorted(v)[len(v) // 2] for k, v in lv.items()}
by = {r['word']: r for r in rows}
out = []
for r in rows:
    if r['level'] in ('C1', 'C2') and src(r) == 'wordfreq' and r['zipf'] >= 3.0 and E.get(r['word'].lower()):
        p = round(pred(E[r['word'].lower()]), 2)
        if r['zipf'] - p >= GAP:
            out.append((r['word'], p, 'coca', r['zipf']))
for w in MANUAL:
    r = by.get(w)
    if not r:
        sys.exit(f'MANUAL 里的 {w} 不在主词典')
    if w not in {o[0] for o in out}:
        out.append((w, min(r['zipf'], LEVEL_ZIPF[r['level']]), 'manual', r['zipf']))
with open(ROOT / 'data/zipf-overrides.tsv', 'w', encoding='utf-8', newline='\n') as f:
    f.write('# 主词典词频修正（scripts/zipf_overrides.py 生成，可手改）。word\tzipf\t来源(coca|manual)\twordfreq 原值\n')
    for o in sorted(out, key=lambda o: -o[3]):
        f.write('\t'.join(map(str, o)) + '\n')
print(f'data/zipf-overrides.tsv {len(out)} 条（coca {sum(o[2] == "coca" for o in out)}，manual {sum(o[2] == "manual" for o in out)}）')
