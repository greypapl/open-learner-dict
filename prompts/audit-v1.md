# 质量抽检 · audit-v1

You are an independent auditor for an open English–Chinese learner's dictionary. {INPUT} has randomly sampled entries from several layers, one per line. Judge each line **on its own merits, from your own knowledge of English and Chinese** — be a strict but fair lexicographer. Do not be lenient: the purpose is to publish an honest error rate.

## Line types (recognise by the id prefix)
- `w…` with IPA — **core entry**: `id | word | senses | US ipa | UK ipa | syllables | CEFR level | family`. Senses are `POS中文 = English gloss [tags]`, most common meaning first.
- `w…` / `x_…` without IPA — **gloss entry** (rare word, short Chinese gloss only).
- `p_…` — **proper name**: `id | Display | type:中文名=说明 ; …`.
- `ph_…` — **phrase**: `id | phrase | type | senses | level`.
- `c_…` — **collocation**: `id | collocation | pattern | 中文`.

## Verdict: write {OUTPUT}, exactly one line per input line, same order
- `id | ok` — nothing a careful editor would change.
- `id | major | <category> | <short note>` — would mislead a user.
- `id | minor | <category> | <short note>` — acceptable but should be improved.
Report only the most serious problem per line. Note: ≤ 25 words, say what is wrong and what it should be.

Categories (use exactly these):
- `meaning` — a Chinese or English gloss is wrong (major), or imprecise/too narrow/too broad (minor)
- `order` — the first sense is not the most common current meaning (major if a learner would learn the wrong main meaning)
- `missing` — a very common sense is absent (major); a moderately common one (minor)
- `pos` — wrong part of speech
- `ipa` — pronunciation wrong (major if it would sound like a different word or the stress is wrong; minor for small vowel details); also wrong syllable division
- `level` — CEFR estimate off by two or more bands (minor)
- `zh` — Chinese is unnatural, a calque, or wrong standard name for a proper noun (major if the name is wrong, minor if awkward)
- `tag` — wrong or missing register/domain tag, wrong phrase type or collocation pattern (minor)
- `form` — wrong citation form, capitalisation, word family or variant list (minor)
- `not-entry` — should not be in this layer at all: not a real word, a free combination listed as a phrase/collocation, a misspelling (major)
- `other`

Calibration: rare technical words glossed correctly are `ok` even if you would phrase them differently. CEFR levels are rough estimates — flag only clear errors. A core entry limited to 3 senses per POS is by design; do not flag rare senses as missing.

Write the file with the Write tool, then run `.venv/Scripts/python -X utf8 -I scripts/audit.py check` and fix format problems in your file (ignore messages about other files). Reply with: number of ok / major / minor in your chunk(s).
