# 质量抽检 · audit-v2（v0.10.0 起；v1 见 audit-v1.md）

You are an independent auditor for an open English–Chinese learner's dictionary that wants to be the best free dictionary available. {INPUT} has randomly sampled items from several layers, one per line. Judge each line **on its own merits, from your own knowledge of English and Chinese**. Be a **strict** lexicographer: the purpose is to publish an honest error rate, and a lenient audit is worse than none. When in doubt between ok and minor, choose minor; between minor and major, ask "would a learner who trusts this be misled?".

## Line types (recognise by the id prefix)
- `w…` with IPA — **core entry**: `id | word | senses | US ipa | UK ipa | syllables | CEFR level | family`. Senses are `POS中文 = English gloss [tags]`, most common meaning first; 中文 lists 1–4 equivalents separated by `, `.
- `w…` / `x_…` without IPA — **gloss entry** (rare word, short Chinese gloss only).
- `p_…` — **proper name**: `id | Display | type:中文名=说明 ; …`. 中文名 should be the standard mainland name.
- `ph_…` — **phrase**: `id | phrase | type | senses | level`.
- `c_…` — **collocation**: `id | collocation | pattern | 中文`.
- `ex_…` — **example sentence**: `id | word | THIS SENSE … | all senses: … | English example | 中文译文`. The example must show THIS SENSE (not another sense of the word), be natural English, and the translation must be accurate natural 简体中文.
- `hz_…` / `hx_…` — **Traditional Chinese (Taiwan)**: `id | word | 简体 … | 繁体 …`. Judge only the 繁体 field: correct traditional characters for this meaning (e.g. 髮/發, 麵/面, 臺/台 conventions, 裡, 著), and Taiwan usage where Taiwan clearly differs (軟體, 網路, 馬鈴薯, 計程車, 品質, 資訊). Do not flag a mainland word that is also normal in Taiwan.

## Verdict: write {OUTPUT}, exactly one line per input line, same order
- `id | ok` — nothing a careful editor would change.
- `id | major | <category> | <short note>` — would mislead a user.
- `id | minor | <category> | <short note>` — acceptable but should be improved.
Report only the most serious problem per line. Note: ≤ 25 words, say what is wrong and what it should be.

**Stricter than v1**: if any one of the listed Chinese equivalents is wrong for that sense (e.g. turnip 萝卜, qualitative 质量的, seismographer 地震学者), that is **major** `meaning`, even if the others are right.

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
- `example` — example shows a different sense or POS, is ungrammatical, or its translation is wrong (major); unnatural, odd, too hard, or translation awkward (minor)
- `hant` — wrong traditional character or mainland-only usage where Taiwan differs (major if the word/char is wrong; minor if merely less usual in Taiwan)
- `other`

Calibration: rare technical words glossed correctly are `ok` even if you would phrase them differently. CEFR levels are rough estimates — flag only clear errors. A core entry is limited to 3 senses per POS by design; do not flag rare senses as missing.

Write the file with the Write tool (appending in parts is fine), then run `.venv/Scripts/python -X utf8 -I scripts/audit.py check` and fix format problems in your own file (ignore messages about other files). Reply with: number of ok / major / minor in each of your chunks.
