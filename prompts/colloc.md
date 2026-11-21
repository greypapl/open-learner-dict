# 搭配层 · colloc-v1

For a learner's English–Chinese dictionary, list the **strongest, most useful collocations** of each headword in {INPUT} (one word per line, frequent words) — the kind given in the Oxford Collocations Dictionary or in a learner's dictionary's "collocations" box. These are combinations that are not idioms (their meaning is mostly transparent) but that learners must learn because the word choice is fixed by usage: *make a decision* (not *do a decision*), *heavy rain*, *highly likely*, *deeply regret*.

## What to include
- Patterns (use exactly these codes):
  - `v+n` — verb + noun object: make a decision, take a risk, pay attention
  - `adj+n` — adjective + noun: heavy rain, strong coffee, close friend
  - `n+n` — noun + noun: a sense of humour, a round of applause, traffic jam
  - `adv+adj` — adverb + adjective: highly likely, fully aware, bitterly cold
  - `v+adv` — verb + adverb: deeply regret, strongly recommend, smile broadly
  - `v+prep` — verb/adj/noun + its fixed preposition: depend on, interested in, reason for
- Per headword: nouns up to 8, verbs and adjectives up to 6, other words 0–3. Only collocations a native speaker would use naturally and that a learner would not guess; choose the strongest, not the most numerous. **Zero is fine** for words with no notable collocations.
- Skip:
  - idioms, phrasal verbs, prepositional phrases (*under review*, *on purpose*) and fixed compounds (*role model*, *road sign*, *chief executive*) — the dictionary has them in a separate phrase layer;
  - proper names (*European Union*);
  - predictable combinations a learner would produce correctly anyway (*write an article*, *large amount*, *football team*, *corporate website*, *big house*). The test: would a Chinese learner be likely to choose a *different* word here? (*make* vs *do* a mistake, *heavy* not *big* rain, *strong* not *thick* coffee). If not, skip it.
- 中文 must be natural Chinese, not a word-for-word rendering of the slots (*range from A to B* → 从…到…不等, not 范围从某物到某物).

## Output: {OUTPUT}

One line per collocation, 4 fields separated by ` | `:

```
collocation | pattern | 中文 | headword
make a decision | v+n | 做决定 | decision
reach a decision | v+n | 作出决定 | decision
heavy rain | adj+n | 大雨 | rain
a round of applause | n+n | 一阵掌声 | applause
highly likely | adv+adj | 很可能 | likely
depend on sth | v+prep | 依靠, 取决于 | depend
```

- **collocation**: lowercase base form; use `sb` / `sth` / `one's` for open slots; include the article if it is normally there (*a round of applause*, *take a risk*).
- **中文**: 1–2 natural Chinese equivalents separated by `, `, each ≤ 12 characters, no brackets, no ；。
- **headword**: the input word this collocation is listed under (copy exactly).
- Group lines by headword in input order. No other text.

Write the file with the Write tool from your own knowledge (several appended parts are fine), then run
`.venv/Scripts/python -X utf8 -I scripts/colloc.py check {NAME}` and fix every error. Reply with the check line only.
