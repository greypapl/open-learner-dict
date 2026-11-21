# 简释层审核 · gloss-review-v1

You review the **gloss layer** of an open English–Chinese dictionary: rare and technical English words (minerals, chemicals, pesticides, plants, animals, anatomy, medicine, law, old words…), each with a short Chinese gloss. An independent audit found about 4% of these glosses wrong — almost always a **wrong Chinese technical term**, e.g.:
- okenite 硅钙石 → 水硅钙石 (硅钙石 is rankinite)
- triallate 燕麦敌 → 野麦畏 (燕麦敌 is diallate)
- explementary 补角的 → 周角互补的 (补角 is supplementary)
- barreler 制桶工 → 装桶工 (制桶工 is cooper)
- nonrelative adj.非相对的 → n.非亲属
- betacism 乙字音 → b音化 (乙字音 is not a word)
- glossapharyngeal → delete (misspelling of glossopharyngeal)

Input lines in {INPUT}: `sense_id | word | pos | 中文 | domain tags`. Several near-synonyms in 中文 are separated by `, `.

## Your job
Check every line from your own knowledge. **Write to {OUTPUT} only lines that need a change**:
- `sense_id | pos | corrected 中文` — the gloss (or POS) is wrong, or one of the listed equivalents is wrong (then give the corrected list, dropping the wrong one), or it is a meaningless/invented Chinese term. Give the standard mainland Chinese term (全国科学技术名词审定委员会 / 药典 / 矿物 naming where it exists), 1–3 items, each ≤ 16 characters, no brackets, no ；。.
- `<entry id> | delete | reason` — the entry id is the sense_id without `.1` / `.2`. Use only when the headword is not a real English word or is a misspelling. **Keep plurals and other inflected forms** (bronchioli, calcanea): they are real forms people look up.

## Do not
- Do not rewrite glosses that are correct but phrased differently from how you would put it; do not add more synonyms to a correct line.
- Do not "fix" a term you are unsure about. If you cannot recall the standard term with reasonable confidence, leave the line out. A wrong correction is worse than no correction.
- Do not change domain tags.

Expect a few changes per hundred lines; most lines are fine. Read every line — do not use scripts to judge.

Write the file with the Write tool (appending in parts is fine), then run `.venv/Scripts/python -X utf8 -I scripts/gloss_review.py check {NAME}` and fix every ✗ error for your chunk. Reply with the check line for your chunk only.
