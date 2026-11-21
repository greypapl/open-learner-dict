"""生成 schema/*.schema.json，并用它们校验发布包里的每一行（不依赖第三方库）。

  python -X utf8 -I scripts/make_schema.py [--version 0.9.0]

Schema 是 JSON Schema draft 2020-12 的子集（type / enum / required / properties / items / additionalProperties / pattern）。
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VER = sys.argv[sys.argv.index('--version') + 1] if '--version' in sys.argv else '0.10.0'
POS = ['n.', 'v.', 'adj.', 'adv.', 'prep.', 'conj.', 'pron.', 'det.', 'int.', 'num.', 'aux.', 'abbr.']
LEVEL = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
S, I, N, B = {'type': 'string'}, {'type': 'integer'}, {'type': 'number'}, {'type': 'boolean'}
SA = {'type': 'array', 'items': S}
REG = {'type': 'array', 'items': {'type': 'string', 'pattern': r'^(formal|informal|slang|dated|literary|uk|us|offensive-mild|offensive-strong|domain:.+)$'}}


def obj(props, optional=()):
    return {'type': 'object', 'properties': props, 'required': [k for k in props if k not in optional], 'additionalProperties': False}


def nullable(t):
    return {'type': [t['type'], 'null'], **{k: v for k, v in t.items() if k != 'type'}}


META = {'type': 'object'}
SCHEMAS = {
    'core': obj({
        'id': {'type': 'string', 'pattern': r'^w\d{6}$'}, 'word': S, 'layer': {'enum': ['core']}, 'rank': I, 'zipf': N, 'zipf_source': {'enum': ['wordfreq', 'level-estimate', 'coca-estimate']},
        'ipa_uk': S, 'ipa_us': S, 'ipa_us_source': {'enum': ['cmu', 'model']}, 'syllables': S,
        'stress': {'type': ['array', 'null'], 'items': {'enum': [0, 1, 2]}},
        'senses': {'type': 'array', 'items': obj({
            'sense_id': S, 'pos': {'enum': POS}, 'zh': S, 'zh_hant': S, 'en_short': S, 'register': REG,
            'synonyms': SA, 'antonyms': SA, 'examples': {'type': 'array', 'items': obj({'en': S, 'zh': S, 'zh_hant': S})}})},
        'inflections': {'type': 'object'}, 'spelling_variants': SA, 'word_family': SA, 'affixes': SA,
        'level': {'enum': LEVEL}, 'level_estimated': B, 'exam_tags': {'type': 'array', 'items': {'enum': ['zk', 'gk', 'cet4', 'cet6', 'ky']}},
        'offensive': {'enum': [None, 'mild', 'strong']}, 'kid_safe': B, 'game_ok': B, 'confidence': {'enum': ['high', 'low']},
        'reviewed': B, 'review_status': {'enum': ['agreed', 'arbitrated', 'disputed']}, 'standard_form': S, 'meta': META},
        optional=('standard_form',)),
    'gloss': obj({
        'id': S, 'word': S, 'layer': {'enum': ['gloss']}, 'zipf': N, 'zipf_source': {'enum': ['wordfreq', 'level-estimate', 'coca-estimate']},
        'senses': {'type': 'array', 'items': obj({'sense_id': S, 'pos': {'enum': POS}, 'zh': S, 'zh_hant': S, 'register': REG})},
        'kid_safe': B, 'confidence': {'enum': ['low', 'medium']}, 'reviewed': B, 'meta': META}),
    'proper': obj({
        'id': {'type': 'string', 'pattern': r'^p_'}, 'word': S, 'display': S, 'layer': {'enum': ['proper']}, 'zipf': N,
        'names': {'type': 'array', 'items': obj({
            'type': {'enum': ['place', 'person', 'brand', 'org', 'abbr', 'work', 'people', 'religion', 'event', 'other']}, 'zh': S, 'zh_hant': S, 'note': S, 'note_hant': S})},
        'also_common': B, 'confidence': {'enum': ['low']}, 'reviewed': B, 'meta': META}),
    'phrases': obj({
        'id': {'type': 'string', 'pattern': r'^ph_'}, 'phrase': S, 'layer': {'enum': ['phrase']}, 'type': {'enum': ['phrv', 'idiom', 'phrase', 'compound']},
        'senses': {'type': 'array', 'items': obj({'sense_id': S, 'pos': {'enum': POS}, 'zh': S, 'zh_hant': S, 'en_short': S, 'register': REG})},
        'level': {'enum': LEVEL}, 'level_estimated': B, 'kid_safe': B, 'confidence': {'enum': ['medium', 'low']}, 'reviewed': B, 'meta': META}),
    'collocations': obj({
        'id': {'type': 'string', 'pattern': r'^c_'}, 'collocation': S, 'layer': {'enum': ['collocation']},
        'pattern': {'enum': ['v+n', 'adj+n', 'n+n', 'adv+adj', 'v+adv', 'adv+v', 'v+prep', 'adj+prep', 'n+prep', 'n+v']}, 'zh': S, 'zh_hant': S, 'headwords': SA,
        'confidence': {'enum': ['medium', 'low']}, 'reviewed': B, 'meta': META}),
    'inflections': obj({
        'form': S, 'lemmas': {'type': 'array', 'items': obj({'lemma': S, 'types': SA})}, 'is_headword': B}),
}
TYPES = {'string': str, 'integer': int, 'number': (int, float), 'boolean': bool, 'array': list, 'object': dict, 'null': type(None)}


def check(v, sch, path=''):
    if 'enum' in sch:
        if v not in sch['enum']:
            return f'{path}: {v!r} 不在枚举中'
        return None
    t = sch.get('type')
    if t:
        ts = t if isinstance(t, list) else [t]
        if not any(isinstance(v, TYPES[x]) and not (x in ('integer', 'number') and isinstance(v, bool)) for x in ts):
            return f'{path}: 类型应为 {t}，实际 {type(v).__name__}'
    if isinstance(v, str) and 'pattern' in sch and not re.search(sch['pattern'], v):
        return f'{path}: {v!r} 不匹配 {sch["pattern"]}'
    if isinstance(v, dict) and 'properties' in sch:
        for k in sch.get('required', []):
            if k not in v:
                return f'{path}: 缺字段 {k}'
        for k, x in v.items():
            if k not in sch['properties']:
                if sch.get('additionalProperties') is False:
                    return f'{path}: 多余字段 {k}'
                continue
            e = check(x, sch['properties'][k], f'{path}.{k}')
            if e:
                return e
    if isinstance(v, list) and 'items' in sch:
        for i, x in enumerate(v):
            e = check(x, sch['items'], f'{path}[{i}]')
            if e:
                return e
    return None


(ROOT / 'schema').mkdir(exist_ok=True)
bad = 0
for name, sch in SCHEMAS.items():
    full = {'$schema': 'https://json-schema.org/draft/2020-12/schema', '$id': f'open-learner-dict/{VER}/{name}.schema.json',
            'title': f'open-learner-dict {name} (one object per JSONL line)', **sch}
    (ROOT / 'schema' / f'{name}.schema.json').write_text(json.dumps(full, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    n = 0
    for i, l in enumerate(open(ROOT / 'release' / VER / 'jsonl' / f'{name}.jsonl', encoding='utf-8'), 1):
        e = check(json.loads(l), sch)
        n += 1
        if e:
            bad += 1
            if bad <= 10:
                print(f'✗ {name}.jsonl 第 {i} 行 {e}')
    print(f'{name}: {n} 行已校验')
sys.exit(1 if bad else 0)
