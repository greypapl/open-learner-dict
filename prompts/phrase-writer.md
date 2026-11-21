# 短语层 · phrase-writer-v1

For a learner's English–Chinese dictionary, list and define the common **multi-word expressions** built on each headword in {INPUT} (one word per line, frequent words). The main dictionary only has single words; this layer adds phrases.

## What to include
Only expressions that a good learner's dictionary (Oxford Advanced Learner's, Longman, Cambridge) lists as their own phrase entry, and that learners up to about C1 actually meet:
- `phrv` — phrasal verbs and prepositional verbs: give up, look after, put up with, run into
- `idiom` — idioms and fixed sayings: break the ice, under the weather, a piece of cake
- `phrase` — fixed grammatical phrases: in spite of, as well as, of course, at least, as soon as, no longer, a lot of, used to
- `compound` — open (spaced) compounds with their own meaning: ice cream, high school, credit card, living room, real estate, mobile phone

Do **not** include: free combinations whose meaning is just the sum of the words (big house, eat lunch, very good), hyphenated or solid compounds (those are single words), proper names, rare/archaic idioms, or a phrase whose only meaning is literal.
Per headword: 0–15 expressions, most important first. Function words and very general words (get, take, put, make, go, come, look, in, on, out) may have many; most words have 0–3. **Zero is fine** — do not pad.

**Go through every headword one by one** and ask four questions: (1) does it form phrasal verbs (reach out, wear off)? (2) fixed phrases with it (on purpose, in stock, take the opportunity)? (3) idioms (sweet tooth, out of reach)? (4) common open compounds where it is the first or second part (stock market, spring break, credit card, alarm clock)? Missing a common expression is as bad as adding a free combination. For 100 frequent words a typical output is 70–150 lines.

## Output: {OUTPUT}

One line per expression, grouped in input order. Each line has 5 fields separated by ` | `:

```
phrase | type | 义项 ; 义项 | 级别 | 标记
give up | phrv | v.放弃, 认输 = to stop trying to do something ; v.戒掉, 戒除 = to stop a habit such as smoking | B1 | -
give in | phrv | v.屈服, 让步 = to finally agree to something after refusing | B2 | -
give away | phrv | v.赠送, 捐赠 = to give something to someone for free ; v.泄露, 暴露 = to show something that was meant to be secret | B2 | -
in spite of | phrase | prep.尽管, 不顾 = without being prevented by something | B1 | -
of course | phrase | adv.当然 = used to say yes or agree strongly | A1 | -
break the ice | idiom | v.打破沉默, 打破僵局 = to make people feel relaxed at first meeting | B2 | -
under the weather | idiom | adj.不舒服, 身体不适 = slightly ill [informal] | C1 | -
ice cream | compound | n.冰淇淋 = a frozen sweet food made from milk or cream | A1 | -
piss off | phrv | v.惹恼, 激怒 = to annoy someone [offensive-mild,uk] ; v.滚开 = go away [offensive-mild] | C1 | nokid
```

- **phrase**: lowercase except where a capital is required; use the base form (give up, not gave up). Use `sb` / `sth` for open slots only when the slot is part of the citation form: `take sth for granted`, `get on sb's nerves`. Use `one's` for possessives: `make up one's mind`.
- **type**: one of `phrv` `idiom` `phrase` `compound`.
- **义项** (same rules as the main dictionary): `POS` immediately followed by 1–4 Chinese expressions separated by `, ` (each ≤ 12 characters, no brackets, no ；。), then ` = ` and an English definition (≤ 12 words, not using the phrase itself), then optional ` [tag,tag]`. Max 4 senses, separated by ` ; `, most common first.
  - POS: `n.` `v.` `adj.` `adv.` `prep.` `conj.` `pron.` `det.` `int.` `num.` (phrasal verbs are `v.`; whole-sentence sayings like "never mind" may use `int.`).
  - tags: `formal` `informal` `slang` `dated` `literary` `uk` `us` `offensive-mild` `offensive-strong` `domain:<领域>` (领域: 医学 法律 经济 金融 商业 政治 计算机 体育 军事 宗教 音乐 烹饪 教育 航海).
- **级别**: CEFR estimate A1–C2.
- **标记**: `-`, or space-separated `low` (not sure) and/or `nokid` (offensive, sexual, drug).
- No ` | ` inside fields; no ` ; ` or ` = ` inside the English definition.

Write the file with the Write tool from your own knowledge (no generating scripts), then run
`.venv/Scripts/python -X utf8 -I scripts/phrase.py check {NAME}` and fix every error it reports.
