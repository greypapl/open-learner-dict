"""数据准备：ECDICT 词头 + wordfreq 排名 + CMUdict → work/headwords.jsonl

用法: .venv/Scripts/python -I scripts/prepare.py [--limit 105000]

只从 ECDICT 读取事实字段：word、exchange、tag、collins、oxford。
**不读取 translation / definition**（释义由 Opus 从零写）。

输出比 10 万多留 5% 缓冲：写手会跳过非原形、不合规专有名词等，跳过的由后面的词补位。
"""
import csv, json, re, sys, argparse
from pathlib import Path
from wordfreq import zipf_frequency

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'sources'
OUT = ROOT / 'work'

ap = argparse.ArgumentParser()
ap.add_argument('--limit', type=int, default=0, help='0 = 不截断')
args = ap.parse_args()

csv.field_size_limit(10**9)

LOWER = re.compile(r"^[a-z]+(?:[-'][a-z]+)*$")
CAP = re.compile(r"^[A-Z][a-z]+$")          # 星期/月份/国家/语言候选，写手再筛
ABBR = re.compile(r"^[A-Z]{2,5}$")          # 高频缩写候选
EXAM = ['zk', 'gk', 'cet4', 'cet6', 'ky']
INFL_KEYS = {'p': 'past', 'd': 'past_participle', 'i': 'present_participle',
             '3': 'third_person', 's': 'plural', 'r': 'comparative', 't': 'superlative'}


def parse_exchange(s):
    d = {}
    for part in s.split('/'):
        if ':' in part:
            k, v = part.split(':', 1)
            d[k] = v
    return d


def is_pure_inflection(ex, collins, oxford):
    """went(0:go/1:p)、children(0:child/1:s) 这类纯屈折形式剔除；
    有柯林斯/牛津标记的（left、running、better）当作独立词保留，交给写手判断。"""
    if '0' not in ex or '1' not in ex:
        return False
    return not collins and not oxford


# ---------- CMUdict → IPA ----------
V = {'AA': 'ɑ', 'AE': 'æ', 'AH': 'ʌ', 'AO': 'ɔ', 'AW': 'aʊ', 'AY': 'aɪ', 'EH': 'ɛ', 'ER': 'ɝ',
     'EY': 'eɪ', 'IH': 'ɪ', 'IY': 'i', 'OW': 'oʊ', 'OY': 'ɔɪ', 'UH': 'ʊ', 'UW': 'u'}
C = {'B': 'b', 'CH': 'tʃ', 'D': 'd', 'DH': 'ð', 'F': 'f', 'G': 'ɡ', 'HH': 'h', 'JH': 'dʒ', 'K': 'k',
     'L': 'l', 'M': 'm', 'N': 'n', 'NG': 'ŋ', 'P': 'p', 'R': 'r', 'S': 's', 'SH': 'ʃ', 'T': 't',
     'TH': 'θ', 'V': 'v', 'W': 'w', 'Y': 'j', 'Z': 'z', 'ZH': 'ʒ'}
ONSETS = {tuple(o.split()) for o in [
    'P R', 'T R', 'K R', 'B R', 'D R', 'G R', 'F R', 'TH R', 'SH R', 'P L', 'K L', 'B L', 'G L', 'F L', 'S L',
    'T W', 'K W', 'D W', 'S W', 'TH W', 'G W', 'S P', 'S T', 'S K', 'S M', 'S N', 'S F',
    'S P R', 'S T R', 'S K R', 'S P L', 'S K W', 'P Y', 'B Y', 'F Y', 'V Y', 'K Y', 'M Y', 'HH Y', 'S K Y', 'S P Y']}


def arpabet_to_ipa(phones):
    """返回 (ipa, stress列表)。重音符放在音节首（最大首音原则的简化版）。"""
    vowels = [i for i, p in enumerate(phones) if p[:2] in V and p[-1].isdigit()]
    if not vowels:
        return ''.join(C.get(p, '') for p in phones), []
    starts = [0]
    for a, b in zip(vowels, vowels[1:]):
        cons = phones[a + 1:b]
        split = len(cons)  # 默认全部归下一音节（再收缩）
        best = b
        for k in range(len(cons) + 1):
            onset = tuple(cons[k:])
            if len(onset) <= 1 or onset in ONSETS:
                best = a + 1 + k
                break
        starts.append(best)
    stress = []
    out = []
    for si, (s, e) in enumerate(zip(starts, starts[1:] + [len(phones)])):
        v = phones[vowels[si]]
        st = int(v[-1])
        stress.append(st)
        mark = '' if len(vowels) == 1 else ('ˈ' if st == 1 else ('ˌ' if st == 2 else ''))  # 单音节不标重音
        syl = ''
        for p in phones[s:e]:
            base = p.rstrip('012')
            if base in V:
                ipa = V[base]
                if base == 'AH' and p.endswith('0'):
                    ipa = 'ə'
                if base == 'ER' and p.endswith('0'):
                    ipa = 'ɚ'
                if base == 'IY' and p.endswith('0') and e == len(phones):
                    ipa = 'i'
                syl += ipa
            else:
                syl += C.get(base, '')
        out.append(mark + syl)
    return ''.join(out), stress


def load_cmu():
    d = {}
    for line in open(SRC / 'cmudict.dict', encoding='utf-8'):
        line = line.split('#')[0].strip()
        if not line:
            continue
        w, *ph = line.split()
        w = re.sub(r'\(\d+\)$', '', w)
        d.setdefault(w, []).append(ph)
    return d


def main():
    cmu = load_cmu()
    best = {}  # lowercase key -> candidate
    zero = {}  # wordfreq 查不到频率的普通词（尾部候选来源）
    with open(SRC / 'ecdict.csv', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            w = row['word'].strip()
            if LOWER.match(w):
                kind = 'word'
            elif CAP.match(w):
                kind = 'proper'
            elif ABBR.match(w):
                kind = 'abbr'
            else:
                continue
            ex = parse_exchange(row['exchange'])
            if is_pure_inflection(ex, row['collins'], row['oxford']):
                continue
            tags = row['tag'].split()
            vetted = bool(row['collins'] or row['oxford'] == '1' or any(t in EXAM for t in tags))
            # 撇号词（he's、don't）不是词头；连字符词 wordfreq 会拆词估频，排名不可信，
            # 只保留有柯林斯/牛津/考纲背书的（well-known、T-shirt）
            if "'" in w or ('-' in w and not vetted):
                continue
            z = zipf_frequency(w, 'en')
            if z <= 0:
                if kind == 'word':
                    zero[w] = row
                continue
            if kind == 'abbr' and z < 3.5:
                continue
            # 专有名词只要进入普通词汇的：有背书或足够高频，写手再按规格筛
            if kind == 'proper' and not vetted and z < 4.0:
                continue
            key = w.lower()
            cand = {
                'word': w, 'kind': kind, 'zipf': z,
                'exam_tags': [t for t in EXAM if t in row['tag'].split()],
                'inflections': {INFL_KEYS[k]: v for k, v in ex.items() if k in INFL_KEYS and v != w},
                'lemma_of': ex.get('0') if '0' in ex else None,
                'collins': int(row['collins'] or 0), 'oxford3000': row['oxford'] == '1',
            }
            prev = best.get(key)
            # 同一小写键：优先小写普通词，其次信息更多的那条
            if prev is None or (prev['kind'] != 'word' and kind == 'word') or \
                    (prev['kind'] == kind and len(cand['exam_tags']) > len(prev['exam_tags'])):
                best[key] = cand

    ranked = sorted(best.values(), key=lambda c: (-c['zipf'], c['word']))
    if args.limit:
        ranked = ranked[:args.limit]
    for c in ranked:
        c['tier'] = 'main'

    # 尾部候选：旧版 29 万词表里、wordfreq 无频率的词，按旧表的词频排名排序
    old_rank = {}
    with open(SRC / 'old-full.csv', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            old_rank.setdefault(row['单词'], int(row['词频排名'] or 10**9))
    tail = []
    for w, row in zero.items():
        if w not in old_rank or w.lower() in best:
            continue
        ex = parse_exchange(row['exchange'])
        tail.append({
            'word': w, 'kind': 'word', 'zipf': 0.0,
            'exam_tags': [t for t in EXAM if t in row['tag'].split()],
            'inflections': {INFL_KEYS[k]: v for k, v in ex.items() if k in INFL_KEYS and v != w},
            'lemma_of': ex.get('0') if '0' in ex else None,
            'collins': int(row['collins'] or 0), 'oxford3000': row['oxford'] == '1',
            'tier': 'tail', 'old_rank': old_rank[w],
        })
    tail.sort(key=lambda c: (c['old_rank'], c['word']))
    ranked += tail
    OUT.mkdir(exist_ok=True)
    n_ipa = 0
    with open(OUT / 'headwords.jsonl', 'w', encoding='utf-8') as out:
        for i, c in enumerate(ranked, 1):
            prons = cmu.get(c['word'].lower(), [])
            ipas = [arpabet_to_ipa(p) for p in prons[:2]]
            if ipas:
                n_ipa += 1
            rec = {
                'id': f'w{i:06d}', 'rank': i, **c,
                'ipa_us_cmu': [x[0] for x in ipas],
                'stress_cmu': ipas[0][1] if ipas else None,
            }
            out.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print(f'main={len(best)} tail={len(tail)} written={len(ranked)} with_cmu={n_ipa}')


if __name__ == '__main__':
    main()
