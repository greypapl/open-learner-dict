"""发布脚本：把 work/merged/ 的各层合成发布版。纯脚本，可重复运行，结果只取决于输入。

  python -X utf8 -I scripts/release.py [--version 0.9.0] [--out release]

输出 release/<version>/：
  jsonl/core.jsonl          主词典（写手 + 审核 + 仲裁）
  jsonl/gloss.jsonl         简释层（冷僻词，一行中文简释；含专名层顺带补的普通漏词）
  jsonl/proper.jsonl        专名层（地名、人名、品牌、机构缩写的中文名）
  jsonl/phrases.jsonl       短语层（短语动词、习语、固定短语、分写复合词）
  jsonl/collocations.jsonl  搭配层
  jsonl/inflections.jsonl   变形索引（went → go）
  csv/*.csv                 同样的数据，表格形式（core 一行一个义项）
  open-learner-dict.sqlite  同样的数据 + lookup 表（任何写法 → 去哪一层找）
  wordlists/*.txt           按考试标签、CEFR 级别拆的纯词表
  MANIFEST.json             版本、条数、各文件 sha256
字段说明见 docs/DATA.md，JSON Schema 见 schema/。

规则：
- 各层统一字段：id、layer、confidence（high / medium / low）、reviewed（是否经过模型审核）。
- 中文释义统一成字符串，多个近义表达用 ", " 分隔（与主词典一致）。
- 主词典 rank：按 wordfreq zipf 从高到低排名（并列按原始频率名次、再按 id），1 起。
- wordfreq 会把带连字符/空格的词拆开算（so-so → so + so），频率严重虚高。这类词（约 340 个）改用估计值：
  同一 CEFR 级别单词 zipf 的中位数，且不高于 wordfreq 原值；zipf_source 标为 level-estimate。简释层没有级别，按 C2 中位数封顶。
- 内部字段（meta、freq_rank_raw、source 等）不进 CSV；JSONL 里保留 meta 供追溯。
- 生成前先应用 work/merged/core-fixes.jsonl（定向修正）和 data/errata.jsonl（勘误）。
- 任何校验不通过都直接退出，不产出半成品。
"""
import csv, glob, hashlib, json, re, sqlite3, sys
from collections import Counter, defaultdict
from pathlib import Path
from wordfreq import zipf_frequency, tokenize
from opencc import OpenCC

ROOT = Path(__file__).resolve().parent.parent
M = ROOT / 'work/merged'
POS = {'n.', 'v.', 'adj.', 'adv.', 'prep.', 'conj.', 'pron.', 'det.', 'int.', 'num.', 'aux.', 'abbr.'}
LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def load(name):
    return [json.loads(l) for l in open(M / name, encoding='utf-8') if l.strip()]


def die(msg):
    sys.exit('✗ 校验失败：' + msg)


def zh_str(z):
    return ', '.join(z) if isinstance(z, list) else z


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


VERSION = arg('--version', '0.10.0')
# 繁体（台湾用词）：
# - 模型校对过的（data/hant-overrides.jsonl，scripts/hant.py 生成，含校对后没改的）直接用；
# - 其余用 OpenCC s2tw（只转字形）+ data/hant-terms.tsv（无歧义的台湾用词表）。
#   不用 s2twp 的词组模式：它偏电脑术语，会把 窗口/视窗 都转成 視窗、类型 转成 型別。
_cc = OpenCC('s2tw')
TERMS = []
if (ROOT / 'data/hant-terms.tsv').exists():
    TERMS = [l.rstrip('\n').split('\t') for l in open(ROOT / 'data/hant-terms.tsv', encoding='utf-8') if l.strip() and not l.startswith('#')]
    TERMS.sort(key=lambda t: -len(t[0]))
HANT = {}
if (ROOT / 'data/hant-overrides.jsonl').exists():
    HANT = {json.loads(l)['key']: json.loads(l)['zh_hant'] for l in open(ROOT / 'data/hant-overrides.jsonl', encoding='utf-8') if l.strip()}
_memo = {}


def hant(key, zh):
    if key in HANT:
        return HANT[key]
    if zh not in _memo:
        t = _cc.convert(zh)
        for a, b in TERMS:
            if a in t:
                t = t.replace(a, b)
        _memo[zh] = t
    return _memo[zh]

OUT = ROOT / arg('--out', 'release') / VERSION

# ---------- 主词典 ----------
core = []
for f in sorted(glob.glob(str(M / 'B[0-9][0-9][0-9][0-9].jsonl'))):
    core += [json.loads(l) for l in open(f, encoding='utf-8') if l.strip()]
# 定向修正（scripts/fixes.py 生成）和勘误（手工维护，data/errata.jsonl：{"sense_id", "zh"?, "en_short"?, "note"}）
by_id = {r['id']: r for r in core}
n_fix = n_err = 0
if (M / 'core-fixes.jsonl').exists():
    for f in load('core-fixes.jsonl'):
        r = by_id[f['id']]
        if 'word' in f:
            r['word'] = f['word']
        if 'standard_form' in f:
            r['standard_form'] = f['standard_form']
        if 'word_family' in f:
            r['word_family'] = f['word_family']
        n_fix += 1
ERR = ROOT / 'data/errata.jsonl'
if ERR.exists():
    senses = {s['sense_id']: s for r in core for s in r['senses']}
    for l in open(ERR, encoding='utf-8'):
        if l.strip():
            e = json.loads(l)
            if e['sense_id'] not in senses:
                die(f'勘误里的 sense_id 不存在：{e["sense_id"]}')
            for k in ('zh', 'en_short'):
                if k in e:
                    senses[e['sense_id']][k] = e[k]
            n_err += 1
multi_tok = lambda w: len(tokenize(w, 'en')) > 1
_lv = defaultdict(list)
for r in core:
    if r.get('zipf') and not multi_tok(r['word']):
        _lv[r['level']].append(r['zipf'])
LEVEL_ZIPF = {k: sorted(v)[len(v) // 2] for k, v in _lv.items()}
n_est = 0
for r in core:
    r['zipf_source'] = 'wordfreq'
    if multi_tok(r['word']):
        r['zipf'] = min(r.get('zipf') or 0, LEVEL_ZIPF[r['level']])
        r['zipf_source'] = 'level-estimate'
        n_est += 1
# 人名、品牌、动词变形同形词的词频修正表（scripts/zipf_overrides.py 生成，可手改）
ZO = ROOT / 'data/zipf-overrides.tsv'
if ZO.exists():
    zo = {l.split('\t')[0]: l.rstrip('\n').split('\t') for l in open(ZO, encoding='utf-8') if l.strip() and not l.startswith('#')}
    hit = 0
    for r in core:
        if r['word'] in zo:
            _, z, how, _orig = zo[r['word']]
            r['zipf'] = min(r.get('zipf') or 0, float(z))
            r['zipf_source'] = 'coca-estimate' if how == 'coca' else 'level-estimate'
            hit += 1; n_est += 1
    if hit != len(zo):
        die(f'zipf-overrides.tsv 里有 {len(zo) - hit} 个词不在主词典')
core.sort(key=lambda r: (-(r.get('zipf') or 0), r.get('freq_rank_raw') or 10 ** 9, r['id']))
seen_id, seen_word = set(), set()
for i, r in enumerate(core, 1):
    if r['id'] in seen_id or r['word'] in seen_word:
        die(f'主词典重复：{r["id"]} {r["word"]}')
    seen_id.add(r['id']); seen_word.add(r['word'])
    if not r['senses']:
        die(f'{r["word"]} 没有义项')
    for s in r['senses']:
        if s['pos'] not in POS or not s['zh'] or not s['en_short']:
            die(f'{r["word"]} 义项不完整：{s}')
    if r['level'] not in LEVELS:
        die(f'{r["word"]} 级别非法')
    r['rank'] = i
    for s in r['senses']:
        s['zh_hant'] = hant(s['sense_id'], s['zh'])
    r['layer'] = 'core'
    r['reviewed'] = True
    r.pop('freq_rank_raw', None)
# 例句（scripts/examples.py 生成：work/merged/examples.jsonl {sense_id, en, zh, reviewed, revised}）；繁体：hant.py X 块校对过要改的用覆盖，其余安全转换
EX = {}
if (M / 'examples.jsonl').exists():
    EX = {e['sense_id']: e for e in load('examples.jsonl')}
n_ex = 0
for r in core:
    for s in r['senses']:
        if s['sense_id'] in EX:
            e = EX[s['sense_id']]
            s['examples'] = [{'en': e['en'], 'zh': e['zh'], 'zh_hant': hant('ex:' + s['sense_id'], e['zh'])}]
            n_ex += 1
if len(EX) != n_ex:
    die(f'例句里有 {len(EX) - n_ex} 条 sense_id 不在主词典里')
core_words = {r['word'] for r in core}
core_lower = {r['word'].lower() for r in core}

# ---------- 简释层（gloss + 专名层顺带补的普通漏词）----------
gloss = []
for r in load('gloss.jsonl'):
    gloss.append({'id': r['id'], 'word': r['word'], 'source': r['source'], 'flags': r['flags'], 'senses': r['senses']})
for r in load('proper-common.jsonl'):
    gloss.append({'id': 'x_' + slug(r['word']), 'word': r['word'], 'source': r['source'], 'flags': r['flags'], 'senses': r['senses']})
if (M / 'phrase-solid.jsonl').exists():  # 短语层里其实应连写或加连字符的词（double-check）：主词典没有的转进简释层
    for r in load('phrase-solid.jsonl'):
        gloss.append({'id': 'x_' + slug(r['solid_form']), 'word': r['solid_form'], 'source': 'phrase-solid', 'flags': r['flags'], 'senses': r['senses']})
out_gloss, seen = [], set()
for r in gloss:
    if r['word'].lower() in core_lower or r['word'].lower() in seen:
        continue  # 主词典已有的不重复收
    seen.add(r['word'].lower())
    senses = []
    for i, s in enumerate(r['senses'], 1):
        if s['pos'] not in POS:
            die(f'gloss {r["word"]} 词性非法')
        z = zh_str(s['zh'])
        senses.append({'sense_id': f'{r["id"]}.{i}', 'pos': s['pos'], 'zh': z, 'zh_hant': hant(f'{r["id"]}.{i}', z), 'register': s['tags']})
    gz = round(zipf_frequency(r['word'], 'en'), 2)
    est = multi_tok(r['word'])
    out_gloss.append({'id': r['id'], 'word': r['word'], 'layer': 'gloss', 'zipf': min(gz, LEVEL_ZIPF['C2']) if est else gz,
                      'zipf_source': 'level-estimate' if est else 'wordfreq',
                      'senses': senses, 'kid_safe': 'nokid' not in r['flags'], 'confidence': 'low', 'reviewed': False,
                      'meta': {'source': r['source']}})
gloss_lower = {r['word'].lower() for r in out_gloss}

# ---------- 专名层 ----------
out_proper = []
for r in load('proper.jsonl'):
    if r['word'] in core_lower:
        continue
    out_proper.append({'id': 'p_' + slug(r['word']), 'word': r['word'], 'display': r['display'], 'layer': 'proper', 'zipf': r['zipf'],
                       'names': [dict(n, zh_hant=hant(f"p_{slug(r['word'])}#{i}", n['zh']), note_hant=hant('', n['note']) if n['note'] else '')
                                 for i, n in enumerate(r['names'], 1)], 'also_common': r['also_common'], 'confidence': 'low', 'reviewed': False,
                       'meta': {'source': r['source']}})
if len({r['id'] for r in out_proper}) != len(out_proper):
    die('专名层 id 重复')

# ---------- 短语层 ----------
out_phr, seen = [], set()
for r in load('phrases.jsonl'):
    pid = 'ph_' + slug(r['phrase'])
    if pid in seen:
        continue  # 只差大小写或标点的重复
    seen.add(pid)
    if r['level'] not in LEVELS:
        die(f'短语 {r["phrase"]} 级别非法')
    senses = [{'sense_id': f'{pid}.{i}', 'pos': s['pos'], 'zh': zh_str(s['zh']), 'zh_hant': hant(f'{pid}.{i}', zh_str(s['zh'])),
               'en_short': s['en_short'], 'register': s['tags']}
              for i, s in enumerate(r['senses'], 1)]
    out_phr.append({'id': pid, 'phrase': r['phrase'], 'layer': 'phrase', 'type': r['type'], 'senses': senses, 'level': r['level'],
                    'level_estimated': True, 'kid_safe': 'nokid' not in r['flags'],
                    'confidence': 'low' if 'low' in r['flags'] else 'medium', 'reviewed': True,
                    'meta': {'source': r['source'], 'review': r['review_status']}})

# ---------- 搭配层 ----------
out_col = []
for r in load('collocations.jsonl'):
    out_col.append({'id': 'c_' + slug(r['collocation']), 'collocation': r['collocation'], 'layer': 'collocation', 'pattern': r['pattern'],
                    'zh': zh_str(r['zh']), 'zh_hant': hant('c_' + slug(r['collocation']), zh_str(r['zh'])), 'headwords': r['headword'], 'confidence': r['confidence'],
                    'reviewed': r.get('review_status', '').startswith('reviewer'),
                    'meta': {'source': r['source'], 'review': r.get('review_status')}})
if len({r['id'] for r in out_col}) != len(out_col):
    die('搭配层 id 重复')

# ---------- 变形索引 ----------
known = core_words | {r['word'] for r in out_gloss}
out_inf = []
for r in load('inflections.jsonl'):
    f = r['form']
    lem = [l for l in r['lemmas'] if l['lemma'] in known]
    if not lem or (f.isupper() and len(f) > 1 and all(l['lemma'].islower() for l in lem)):
        continue  # ECDICT 里全大写的重复形式（ACES → ace）
    out_inf.append({'form': f, 'lemmas': [{'lemma': l['lemma'], 'types': l['types']} for l in lem], 'is_headword': f in known})

# ---------- 写文件 ----------
(OUT / 'jsonl').mkdir(parents=True, exist_ok=True)
(OUT / 'csv').mkdir(exist_ok=True)
(OUT / 'wordlists').mkdir(exist_ok=True)


def wjsonl(name, rows):
    with open(OUT / 'jsonl' / name, 'w', encoding='utf-8', newline='\n') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')


def wcsv(name, header, rows):
    with open(OUT / 'csv' / name, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


J = lambda x: ', '.join(x) if x else ''
wjsonl('core.jsonl', core); wjsonl('gloss.jsonl', out_gloss); wjsonl('proper.jsonl', out_proper)
wjsonl('phrases.jsonl', out_phr); wjsonl('collocations.jsonl', out_col); wjsonl('inflections.jsonl', out_inf)

wcsv('core.csv', ['id', 'word', 'standard_form', 'rank', 'zipf', 'zipf_source', 'sense_id', 'pos', 'zh', 'zh_hant', 'en_short', 'register', 'ipa_us', 'ipa_uk', 'syllables', 'level',
                  'exam_tags', 'word_family', 'spelling_variants', 'offensive', 'kid_safe', 'game_ok', 'confidence', 'review_status'],
     [[r['id'], r['word'], r.get('standard_form', ''), r['rank'], r['zipf'], r['zipf_source'], s['sense_id'], s['pos'], s['zh'], s['zh_hant'], s['en_short'], J(s['register']), r['ipa_us'], r['ipa_uk'],
       r['syllables'], r['level'], J(r['exam_tags']), J(r['word_family']), J(r['spelling_variants']), r['offensive'] or '',
       int(r['kid_safe']), int(r['game_ok']), r['confidence'], r['review_status']] for r in core for s in r['senses']])
wcsv('gloss.csv', ['id', 'word', 'zipf', 'sense_id', 'pos', 'zh', 'zh_hant', 'register', 'kid_safe'],
     [[r['id'], r['word'], r['zipf'], s['sense_id'], s['pos'], s['zh'], s['zh_hant'], J(s['register']), int(r['kid_safe'])] for r in out_gloss for s in r['senses']])
wcsv('proper.csv', ['id', 'word', 'display', 'zipf', 'type', 'zh', 'zh_hant', 'note', 'note_hant', 'also_common'],
     [[r['id'], r['word'], r['display'], r['zipf'], n['type'], n['zh'], n['zh_hant'], n['note'], n['note_hant'], int(r['also_common'])] for r in out_proper for n in r['names']])
wcsv('phrases.csv', ['id', 'phrase', 'type', 'sense_id', 'pos', 'zh', 'zh_hant', 'en_short', 'register', 'level', 'kid_safe', 'confidence'],
     [[r['id'], r['phrase'], r['type'], s['sense_id'], s['pos'], s['zh'], s['zh_hant'], s['en_short'], J(s['register']), r['level'], int(r['kid_safe']),
       r['confidence']] for r in out_phr for s in r['senses']])
wcsv('collocations.csv', ['id', 'collocation', 'pattern', 'zh', 'zh_hant', 'headwords', 'confidence'],
     [[r['id'], r['collocation'], r['pattern'], r['zh'], r['zh_hant'], J(r['headwords']), r['confidence']] for r in out_col])
wcsv('examples.csv', ['sense_id', 'entry_id', 'word', 'en', 'zh', 'zh_hant'],
     [[s['sense_id'], r['id'], r['word'], e['en'], e['zh'], e['zh_hant']] for r in core for s in r['senses'] for e in s['examples']])
wcsv('inflections.csv', ['form', 'lemma', 'types', 'is_headword'],
     [[r['form'], l['lemma'], J(l['types']), int(r['is_headword'])] for r in out_inf for l in r['lemmas']])

# 纯词表
by = defaultdict(list)
for r in core:
    for t in r['exam_tags']:
        by['exam-' + t].append(r['word'])
    by['cefr-' + r['level']].append(r['word'])
    if r['game_ok'] and r['kid_safe']:
        by['game-kid-safe'].append(r['word'])
for k, ws in by.items():
    (OUT / 'wordlists' / f'{k}.txt').write_text('\n'.join(ws) + '\n', encoding='utf-8', newline='\n')

# SQLite
db = OUT / 'open-learner-dict.sqlite'
db.unlink(missing_ok=True)
con = sqlite3.connect(db)
con.executescript('''
CREATE TABLE entries(id TEXT PRIMARY KEY, word TEXT NOT NULL, standard_form TEXT, layer TEXT NOT NULL, rank INTEGER, zipf REAL, zipf_source TEXT, ipa_us TEXT, ipa_uk TEXT,
  syllables TEXT, level TEXT, exam_tags TEXT, word_family TEXT, spelling_variants TEXT, affixes TEXT, inflections TEXT, offensive TEXT,
  kid_safe INTEGER, game_ok INTEGER, confidence TEXT, reviewed INTEGER, review_status TEXT);
CREATE TABLE senses(sense_id TEXT PRIMARY KEY, entry_id TEXT NOT NULL, idx INTEGER, pos TEXT, zh TEXT, zh_hant TEXT, en_short TEXT, register TEXT);
CREATE TABLE examples(sense_id TEXT NOT NULL, idx INTEGER, en TEXT NOT NULL, zh TEXT, zh_hant TEXT);
CREATE TABLE proper(id TEXT PRIMARY KEY, word TEXT NOT NULL, display TEXT, zipf REAL, also_common INTEGER, confidence TEXT);
CREATE TABLE proper_names(proper_id TEXT NOT NULL, idx INTEGER, type TEXT, zh TEXT, zh_hant TEXT, note TEXT, note_hant TEXT);
CREATE TABLE phrases(id TEXT PRIMARY KEY, phrase TEXT NOT NULL, type TEXT, level TEXT, kid_safe INTEGER, confidence TEXT);
CREATE TABLE phrase_senses(sense_id TEXT PRIMARY KEY, phrase_id TEXT NOT NULL, idx INTEGER, pos TEXT, zh TEXT, zh_hant TEXT, en_short TEXT, register TEXT);
CREATE TABLE collocations(id TEXT PRIMARY KEY, collocation TEXT NOT NULL, pattern TEXT, zh TEXT, zh_hant TEXT, confidence TEXT);
CREATE TABLE collocation_headwords(collocation_id TEXT NOT NULL, headword TEXT NOT NULL);
CREATE TABLE inflections(form TEXT NOT NULL, lemma TEXT NOT NULL, types TEXT, is_headword INTEGER);
CREATE TABLE lookup(key TEXT NOT NULL, layer TEXT NOT NULL, id TEXT NOT NULL);
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
''')
js = lambda x: json.dumps(x, ensure_ascii=False)
con.executemany('INSERT INTO entries VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                [(r['id'], r['word'], r.get('standard_form'), 'core', r['rank'], r['zipf'], r['zipf_source'], r['ipa_us'], r['ipa_uk'], r['syllables'], r['level'], js(r['exam_tags']),
                  js(r['word_family']), js(r['spelling_variants']), js(r['affixes']), js(r['inflections']), r['offensive'], int(r['kid_safe']),
                  int(r['game_ok']), r['confidence'], 1, r['review_status']) for r in core] +
                [(r['id'], r['word'], None, 'gloss', None, r['zipf'], r['zipf_source'], None, None, None, None, '[]', '[]', '[]', '[]', '{}', None, int(r['kid_safe']),
                  None, 'low', 0, None) for r in out_gloss])
con.executemany('INSERT INTO senses VALUES(?,?,?,?,?,?,?,?)',
                [(s['sense_id'], r['id'], i, s['pos'], s['zh'], s.get('zh_hant'), s.get('en_short'), js(s['register']))
                 for r in core + out_gloss for i, s in enumerate(r['senses'], 1)])
con.executemany('INSERT INTO examples VALUES(?,?,?,?,?)',
                [(s['sense_id'], i, e['en'], e['zh'], e['zh_hant']) for r in core for s in r['senses'] for i, e in enumerate(s['examples'], 1)])
con.executemany('INSERT INTO proper VALUES(?,?,?,?,?,?)', [(r['id'], r['word'], r['display'], r['zipf'], int(r['also_common']), 'low') for r in out_proper])
con.executemany('INSERT INTO proper_names VALUES(?,?,?,?,?,?,?)', [(r['id'], i, n['type'], n['zh'], n['zh_hant'], n['note'], n['note_hant']) for r in out_proper for i, n in enumerate(r['names'], 1)])
con.executemany('INSERT INTO phrases VALUES(?,?,?,?,?,?)', [(r['id'], r['phrase'], r['type'], r['level'], int(r['kid_safe']), r['confidence']) for r in out_phr])
con.executemany('INSERT INTO phrase_senses VALUES(?,?,?,?,?,?,?,?)',
                [(s['sense_id'], r['id'], i, s['pos'], s['zh'], s['zh_hant'], s['en_short'], js(s['register'])) for r in out_phr for i, s in enumerate(r['senses'], 1)])
con.executemany('INSERT INTO collocations VALUES(?,?,?,?,?,?)', [(r['id'], r['collocation'], r['pattern'], r['zh'], r['zh_hant'], r['confidence']) for r in out_col])
con.executemany('INSERT INTO collocation_headwords VALUES(?,?)', [(r['id'], h) for r in out_col for h in r['headwords']])
con.executemany('INSERT INTO inflections VALUES(?,?,?,?)', [(r['form'], l['lemma'], J(l['types']), int(r['is_headword'])) for r in out_inf for l in r['lemmas']])
lk = [(r['word'].lower(), r['layer'], r['id']) for r in core + out_gloss + out_proper]
lk += [(r['phrase'].lower(), 'phrase', r['id']) for r in out_phr] + [(r['collocation'].lower(), 'collocation', r['id']) for r in out_col]
ids = {r['word']: r['id'] for r in core + out_gloss}
lk += [(r['form'].lower(), 'inflection', ids[l['lemma']]) for r in out_inf for l in r['lemmas']]
con.executemany('INSERT INTO lookup VALUES(?,?,?)', sorted(set(lk)))
con.executescript('''
CREATE INDEX idx_entries_word ON entries(word COLLATE NOCASE); CREATE INDEX idx_entries_rank ON entries(rank);
CREATE INDEX idx_senses_entry ON senses(entry_id); CREATE INDEX idx_lookup_key ON lookup(key);
CREATE INDEX idx_phrases_phrase ON phrases(phrase COLLATE NOCASE); CREATE INDEX idx_psenses ON phrase_senses(phrase_id);
CREATE INDEX idx_colhw ON collocation_headwords(headword); CREATE INDEX idx_infl ON inflections(form COLLATE NOCASE);
CREATE INDEX idx_pnames ON proper_names(proper_id); CREATE INDEX idx_examples ON examples(sense_id);
''')
counts = {'core': len(core), 'core_senses': sum(len(r['senses']) for r in core), 'gloss': len(out_gloss), 'proper': len(out_proper),
          'phrases': len(out_phr), 'collocations': len(out_col), 'inflections': len(out_inf), 'examples': n_ex}
con.executemany('INSERT INTO meta VALUES(?,?)', [('version', VERSION), ('license', 'CC BY-SA 4.0')] + [(k, str(v)) for k, v in counts.items()])
con.commit(); con.execute('VACUUM'); con.close()

# 清单
files = {}
for p in sorted(OUT.rglob('*')):
    if p.is_file() and p.name != 'MANIFEST.json':
        files[p.relative_to(OUT).as_posix()] = {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
stats = {'core_confidence': dict(Counter(r['confidence'] for r in core)), 'core_review_status': dict(Counter(r['review_status'] for r in core)),
         'core_level': dict(Counter(r['level'] for r in core)), 'phrase_type': dict(Counter(r['type'] for r in out_phr)),
         'phrase_level': dict(Counter(r['level'] for r in out_phr)), 'collocation_pattern': dict(Counter(r['pattern'] for r in out_col)),
         'zh_hant_reviewed': len(HANT),
         'examples_filled': sum(1 for r in core for s in r['senses'] if s.get('examples'))}
(OUT / 'MANIFEST.json').write_text(json.dumps({'name': 'open-learner-dict', 'version': VERSION, 'license': 'CC BY-SA 4.0',
                                               'counts': counts, 'stats': stats, 'files': files}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'  定向修正 {n_fix} 条，勘误 {n_err} 条，词频估计 {n_est} 条')
print(f'✓ release/{VERSION}：' + '，'.join(f'{k} {v}' for k, v in counts.items()))
print('  文件：' + '，'.join(f'{k} {v["bytes"] / 1e6:.1f}MB' for k, v in files.items() if v['bytes'] > 2e6))
