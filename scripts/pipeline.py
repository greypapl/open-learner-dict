"""批次后处理。

  python -I scripts/pipeline.py disputes <批次>   # 写手+审核 → work/raw/<批次>.disputes.jsonl（交给仲裁）
  python -I scripts/pipeline.py merge <批次>      # 写手+审核+仲裁 → work/merged/<批次>.jsonl（最终词条）
  python -I scripts/pipeline.py review-md <批次>... # 生成人工过目用的 Markdown（试点用）
"""
import json, sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'work' / 'raw'
MERGED = ROOT / 'work' / 'merged'
PROMPT_VER = {'writer': 'writer-v2', 'reviewer': 'reviewer-v2', 'arbiter': 'arbiter-v1'}
MODELS = {'writer': 'claude-opus-5-5', 'reviewer': 'claude-opus-5-5', 'arbiter': 'claude-fable-5-2'}


def jl(p):
    p = Path(p)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding='utf-8-sig').splitlines() if l.strip()]


def by_id(rows):
    return {r['id']: r for r in rows}


def headwords():
    return by_id(jl(ROOT / 'work' / 'headwords.jsonl'))


def disputes(b):
    w = by_id(jl(RAW / f'{b}.writer.jsonl'))
    out = []
    for r in jl(RAW / f'{b}.reviewer.jsonl'):
        if r.get('verdict') == 'fix':
            out.append({'id': r['id'], 'word': r['word'], 'writer': w[r['id']],
                        'issues': r.get('issues', []), 'fixed': r['fixed']})
    p = RAW / f'{b}.disputes.jsonl'
    p.write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in out), encoding='utf-8')
    if out:
        import compact
        compact.disputes_txt(b)   # 仲裁读紧凑版 <B>.disputes.txt
    print(f'{p.relative_to(ROOT)} {len(out)}')


def finalize(e, hw, status, review_note):
    """把模型词条和事实字段合成为 SPEC §4 的最终结构。skip 的返回 None。"""
    if e.get('skip'):
        return None
    senses = []
    for i, s in enumerate(e['senses'], 1):
        senses.append({'sense_id': f"{hw['id']}.{i}", 'pos': s['pos'], 'zh': s['zh'],
                       'zh_hant': None,  # 由 OpenCC 批量填充
                       'en_short': s['en_short'], 'register': s.get('register', []),
                       'synonyms': [], 'antonyms': [], 'examples': []})
    w = e['word']
    game_ok = hw['kind'] == 'word' and w.isalpha() and w.islower()
    low = e.get('confidence') == 'low' or status == 'disputed' or e.get('ipa_source') == 'model'
    return {
        'id': hw['id'], 'word': w, 'rank': None,  # 最终排名在全部完成、剔除 skip 后重排
        'freq_rank_raw': hw['rank'], 'zipf': hw['zipf'],
        'ipa_uk': e['ipa_uk'], 'ipa_us': e['ipa_us'], 'ipa_us_source': e['ipa_source'],
        'syllables': e['syllables'],
        'stress': hw['stress_cmu'] if e['ipa_source'] == 'cmu' else None,
        'senses': senses,
        'inflections': hw['inflections'],
        'spelling_variants': e['spelling_variants'], 'word_family': e['word_family'],
        'affixes': e['affixes'],
        'level': e['level'], 'level_estimated': True,
        'exam_tags': hw['exam_tags'],
        'offensive': e['offensive'], 'kid_safe': e['kid_safe'], 'game_ok': game_ok,
        'confidence': 'low' if low else 'high',
        'review_status': status,
        'meta': {'models': MODELS, 'prompt_ver': PROMPT_VER, 'review': review_note},
    }


def prompt_ver(b):
    """按批次实际产物判断提示词版本：有 .txt 紧凑产物的是 v3。"""
    v3 = (RAW / f'{b}.writer.txt').exists()
    return {'writer': 'writer-v3' if v3 else 'writer-v2',
            'reviewer': 'reviewer-v3' if (RAW / f'{b}.reviewer.txt').exists() else 'reviewer-v2',
            'arbiter': 'arbiter-v2' if (RAW / f'{b}.arbiter.txt').exists() else 'arbiter-v1'}


def merge(b):
    hw = headwords()
    w = jl(RAW / f'{b}.writer.jsonl')
    rv = by_id(jl(RAW / f'{b}.reviewer.jsonl'))
    ar = by_id(jl(RAW / f'{b}.arbiter.jsonl'))
    MERGED.mkdir(parents=True, exist_ok=True)
    stats = {'agreed': 0, 'arbitrated': 0, 'disputed': 0, 'skip': 0, 'missing_arbiter': 0}
    out, skips = [], []
    for e in w:
        r = rv.get(e['id'], {'verdict': 'ok'})
        if r['verdict'] == 'ok':
            final, status, note = e, 'agreed', 'reviewer ok'
        elif e['id'] in ar:
            a = ar[e['id']]
            final = a['final']
            status = 'disputed' if a['decision'] == 'disputed' else 'arbitrated'
            note = f"arbiter:{a['decision']} {a.get('note', '')}"
        else:
            stats['missing_arbiter'] += 1
            continue
        rec = finalize(final, hw[e['id']], status, note)
        if rec is not None:
            wm = RAW / f'{b}.writer.model'   # 个别批次由其他模型写（如 fable），在此记录
            if wm.exists():
                rec['meta']['models'] = {**MODELS, 'writer': wm.read_text().strip()}
            rec['meta']['prompt_ver'] = prompt_ver(b)
            we = RAW / f'{b}.writer.effort'  # 写手思考强度（A/B 测试用）
            if we.exists():
                rec['meta']['writer_effort'] = we.read_text().strip()
        if rec is None:
            stats['skip'] += 1
            skips.append({'id': e['id'], 'word': e['word'], 'skip': final.get('skip')})
            continue
        stats[status] += 1
        out.append(rec)
    (MERGED / f'{b}.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in out), encoding='utf-8')
    (MERGED / f'{b}.skips.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in skips), encoding='utf-8')
    print(b, stats)


def review_md(batches):
    lines = ['# 试点结果过目表', '',
             '标记说明：✅ 写手与审核一致 · ⚖️ 仲裁后 · ⚠️ 存疑（删了无法确认的义项） · ⏭️ 跳过', '']
    rows = []
    for b in batches:
        for x in jl(MERGED / f'{b}.jsonl'):
            rows.append((x['freq_rank_raw'], 'keep', x))
        for x in jl(MERGED / f'{b}.skips.jsonl'):
            rows.append((headwords()[x['id']]['rank'], 'skip', x))
    rows.sort(key=lambda t: t[0])
    icon = {'agreed': '✅', 'arbitrated': '⚖️', 'disputed': '⚠️'}
    for rank, kind, x in rows:
        if kind == 'skip':
            lines.append(f"- ⏭️ **{x['word']}** `#{rank}` — 跳过：{x['skip']}")
            continue
        head = (f"- {icon[x['review_status']]} **{x['word']}** `#{rank}` /{x['ipa_us']}/ "
                f"英 /{x['ipa_uk']}/ · {x['syllables']} · {x['level']}"
                + (' · 🔒非儿童' if not x['kid_safe'] else '')
                + (' · 低置信' if x['confidence'] == 'low' else ''))
        lines.append(head)
        for s in x['senses']:
            reg = f" `{' '.join(s['register'])}`" if s['register'] else ''
            lines.append(f"  - {s['pos']} {s['zh']} — *{s['en_short']}*{reg}")
        extra = []
        if x['word_family']:
            extra.append('词族: ' + ', '.join(x['word_family']))
        if x['affixes']:
            extra.append('词缀: ' + ' '.join(x['affixes']))
        if x['spelling_variants']:
            extra.append('变体: ' + ', '.join(x['spelling_variants']))
        if x['review_status'] != 'agreed':
            extra.append('审核: ' + x['meta']['review'])
        if extra:
            lines.append('  - <sub>' + ' · '.join(extra) + '</sub>')
    p = ROOT / 'reports' / 'pilot-review.md'
    p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(p.relative_to(ROOT), len(rows))


if __name__ == '__main__':
    cmd, *bs = sys.argv[1:]
    if cmd == 'disputes':
        [disputes(b) for b in bs]
    elif cmd == 'merge':
        [merge(b) for b in bs]
    elif cmd == 'review-md':
        review_md(bs)
