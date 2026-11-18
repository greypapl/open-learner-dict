"""v3 紧凑格式 ⇄ 完整 JSON 词条（写手格式）。

紧凑行（每个词头一行，字段用 " | " 分隔）：
  跳过： word | skip:<原因>
  收录： word | 义项 | 美音 | 英音 | 音节 | 词族 | 词缀 | 异体 | 级别 | 标记
  义项： pos+zh = en_short [register,...]   多个义项用 " ; " 分隔
  美音： "=" 取 CMU 第 1 个读音，"=2" 取第 2 个；否则写音标（与 CMU 某读音相同则仍记 cmu，否则 model）
  英音： "=" 表示与美音相同；音节："=" 表示与原词相同；列表字段用 ", " 分隔，空写 "-"
  标记： "-" 或空格分隔的 low / nokid / mild / strong（mild/strong 自动 kid_safe=false）

  python -I scripts/compact.py expand writer|reviewer|arbiter <批次>...
      writer:   raw/<B>.writer.txt      → raw/<B>.writer.jsonl
      reviewer: raw/<B>.reviewer.txt    → raw/<B>.reviewer.jsonl   （只列 fix；其余补 ok）
      arbiter:  raw/<B>.arbiter.txt     → raw/<B>.arbiter.jsonl
  python -I scripts/compact.py disputes <批次>...   raw/<B>.disputes.jsonl → raw/<B>.disputes.txt（给仲裁看的紧凑版）
  python -I scripts/compact.py roundtrip <批次>...  自检：旧 JSON → 紧凑 → JSON 是否一致
"""
import json, sys, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'work' / 'raw'
BATCHES = ROOT / 'work' / 'batches'
POS = sorted(['n.', 'v.', 'adj.', 'adv.', 'prep.', 'conj.', 'pron.', 'det.', 'int.', 'num.', 'aux.', 'abbr.'],
             key=len, reverse=True)
SEP = ' | '


class FormatError(Exception):
    pass


def jl(p):
    p = Path(p)
    return [json.loads(l) for l in p.read_text(encoding='utf-8-sig').splitlines() if l.strip()] if p.exists() else []


def dump(p, rows):
    Path(p).write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in rows),
                       encoding='utf-8')


def lst(s):
    s = s.strip()
    return [] if s in ('-', '') else [x.strip() for x in s.split(',') if x.strip()]


def parse_sense(s):
    s = s.strip()
    pos = next((p for p in POS if s.startswith(p)), None)
    if not pos:
        raise FormatError(f'义项缺词性: {s}')
    rest = s[len(pos):]
    reg = []
    m = re.search(r'(\s*\[[^\]]*\])+\s*$', rest)   # 允许 [a,b] 或 [a] [b]
    if m:
        for grp in re.findall(r'\[([^\]]*)\]', m.group(0)):
            reg += [x.strip() for x in grp.split(',') if x.strip()]
        rest = rest[:m.start()]
    if ' = ' not in rest:
        raise FormatError(f'义项缺 " = " 英文简释: {s}')
    zh, en = rest.split(' = ', 1)
    return {'pos': pos, 'zh': zh.strip(), 'en_short': en.strip(), 'register': reg}


def from_compact(line, hw):
    """紧凑行 + 输入词头 → 完整词条。hw 至少含 id、word、ipa_us_cmu。"""
    f = [x.strip() for x in line.strip().split(SEP)]
    word = f[0]
    if word != hw['word']:
        raise FormatError(f'词头对不上: 期望 {hw["word"]}，得到 {word}')
    if len(f) == 2 and f[1].startswith('skip:'):
        return {'id': hw['id'], 'word': word, 'skip': f[1][5:].strip()}
    if len(f) != 10:
        raise FormatError(f'{word}: 应有 10 个字段，实际 {len(f)}')
    _, senses, us, uk, syl, fam, aff, var, lvl, flags = f
    cmu = hw.get('ipa_us_cmu') or []
    if us.startswith('='):
        k = int(us[1:] or 1)
        if not 1 <= k <= len(cmu):
            raise FormatError(f'{word}: 美音 {us} 但 CMU 只有 {len(cmu)} 个读音')
        us, src = cmu[k - 1], 'cmu'
    else:
        src = 'cmu' if us in cmu else 'model'
    fl = flags.split() if flags not in ('-', '') else []
    bad = [x for x in fl if x not in ('low', 'nokid', 'mild', 'strong')]
    if bad:
        raise FormatError(f'{word}: 未知标记 {bad}')
    off = 'strong' if 'strong' in fl else 'mild' if 'mild' in fl else None
    return {'id': hw['id'], 'word': word,
            'senses': [parse_sense(s) for s in senses.split(' ; ')],
            'ipa_us': us, 'ipa_uk': us if uk == '=' else uk, 'ipa_source': src,
            'syllables': word if syl == '=' else syl,
            'word_family': lst(fam), 'affixes': lst(aff), 'spelling_variants': lst(var),
            'level': lvl, 'offensive': off, 'kid_safe': not (off or 'nokid' in fl),
            'confidence': 'low' if 'low' in fl else 'high'}


def to_compact(e, hw):
    w = e['word']
    if e.get('skip'):
        return f"{w}{SEP}skip:{e['skip']}"
    ss = []
    for s in e['senses']:
        reg = f" [{','.join(s['register'])}]" if s.get('register') else ''
        ss.append(f"{s['pos']}{s['zh']} = {s['en_short']}{reg}")
    cmu = hw.get('ipa_us_cmu') or []
    us = e['ipa_us']
    if e.get('ipa_source') == 'cmu' and us in cmu:
        k = cmu.index(us) + 1
        us = '=' if k == 1 else f'={k}'
    uk = '=' if e['ipa_uk'] == e['ipa_us'] else e['ipa_uk']
    syl = '=' if e['syllables'] == w else e['syllables']
    L = lambda xs: ', '.join(xs) if xs else '-'
    fl = []
    if e.get('confidence') == 'low':
        fl.append('low')
    if e.get('offensive'):
        fl.append(e['offensive'])
    elif e.get('kid_safe') is False:
        fl.append('nokid')
    return SEP.join([w, ' ; '.join(ss), us, uk, syl, L(e['word_family']), L(e['affixes']),
                     L(e['spelling_variants']), e['level'], ' '.join(fl) or '-'])


def inputs(b):
    return jl(BATCHES / f'{b}.input.jsonl')


def read_lines(p):
    return [l for l in Path(p).read_text(encoding='utf-8-sig').splitlines() if l.strip()]


def expand_writer(b):
    hws, lines = inputs(b), read_lines(RAW / f'{b}.writer.txt')
    errs, out = [], []
    if len(lines) != len(hws):
        errs.append(f'行数 {len(lines)} ≠ 输入 {len(hws)}')
    for i, (hw, line) in enumerate(zip(hws, lines), 1):
        try:
            out.append(from_compact(line, hw))
        except (FormatError, ValueError) as ex:
            errs.append(f'第{i}行 {ex}')
    return out, errs


def locate(hws, r):
    """审核/仲裁行按 word（重名时用 n=行号）找到输入词头。"""
    if 'n' in r:
        return hws[int(r['n']) - 1]
    hit = [h for h in hws if h['word'] == r['word']]
    if len(hit) != 1:
        raise FormatError(f"{r['word']}: 在批次中出现 {len(hit)} 次，请加 \"n\":行号")
    return hit[0]


def expand_reviewer(b):
    hws = inputs(b)
    w = {e['id']: e for e in jl(RAW / f'{b}.writer.jsonl')}
    fixes, errs = {}, []
    for i, line in enumerate(read_lines(RAW / f'{b}.reviewer.txt'), 1):
        try:
            r = json.loads(line)
            hw = locate(hws, r)
            fx = from_compact(r['fixed'], hw)
            if fx != w[hw['id']]:      # 改了等于没改的视为 ok
                fixes[hw['id']] = {'id': hw['id'], 'word': hw['word'], 'verdict': 'fix',
                                   'issues': r.get('issues', []), 'fixed': fx}
        except (FormatError, ValueError, KeyError) as ex:
            errs.append(f'第{i}行 {ex}')
    out = [fixes.get(h['id'], {'id': h['id'], 'word': h['word'], 'verdict': 'ok'}) for h in hws]
    return out, errs


def expand_arbiter(b):
    hws = inputs(b)
    out, errs = [], []
    for i, line in enumerate(read_lines(RAW / f'{b}.arbiter.txt'), 1):
        try:
            r = json.loads(line)
            hw = locate(hws, r)
            out.append({'id': hw['id'], 'word': hw['word'], 'decision': r['decision'],
                        'note': r.get('note', ''), 'final': from_compact(r['final'], hw)})
        except (FormatError, ValueError, KeyError) as ex:
            errs.append(f'第{i}行 {ex}')
    want = {d['id'] for d in jl(RAW / f'{b}.disputes.jsonl')}
    miss = want - {r['id'] for r in out}
    if miss:
        errs.append(f'缺少 {len(miss)} 条分歧的裁决')
    return out, errs


def disputes_txt(b):
    hws = {h['id']: h for h in inputs(b)}
    idx = {h['id']: i for i, h in enumerate(inputs(b), 1)}
    rows = []
    for d in jl(RAW / f'{b}.disputes.jsonl'):
        hw = hws[d['id']]
        rows.append({'n': idx[d['id']], 'word': d['word'], 'ipa_us_cmu': hw.get('ipa_us_cmu') or [],
                     'writer': to_compact(d['writer'], hw), 'issues': d['issues'],
                     'fixed': to_compact(d['fixed'], hw)})
    dump(RAW / f'{b}.disputes.txt', rows)
    return len(rows)


def roundtrip(b):
    hws = {h['id']: h for h in inputs(b)}
    bad = 0
    for e in jl(RAW / f'{b}.writer.jsonl'):
        hw = hws[e['id']]
        back = from_compact(to_compact(e, hw), hw)
        exp = {k: v for k, v in e.items() if k != 'rank'}
        if not e.get('skip'):
            for s in exp['senses']:
                s.setdefault('register', [])
        if back != exp:
            bad += 1
            if bad <= 3:
                print('  ≠', e['word'], {k: (exp.get(k), back.get(k)) for k in exp if exp.get(k) != back.get(k)})
    return bad


if __name__ == '__main__':
    cmd, *args = sys.argv[1:]
    rc = 0
    if cmd == 'expand':
        stage, *bs = args
        fn = {'writer': expand_writer, 'reviewer': expand_reviewer, 'arbiter': expand_arbiter}[stage]
        for b in bs:
            out, errs = fn(b)
            if errs:
                rc = 1
                print(f'✗ {b}.{stage}.txt 有 {len(errs)} 处格式问题（未生成 jsonl）：')
                for x in errs[:40]:
                    print('  ', x)
            else:
                dump(RAW / f'{b}.{stage}.jsonl', out)
                print(f'✓ {b}.{stage}.jsonl {len(out)} 行')
    elif cmd == 'disputes':
        for b in args:
            print(b, 'disputes.txt', disputes_txt(b))
    elif cmd == 'roundtrip':
        for b in args:
            n = roundtrip(b)
            rc |= bool(n)
            print(b, 'roundtrip 不一致', n)
    sys.exit(rc)
