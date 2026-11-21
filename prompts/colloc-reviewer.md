# 搭配层 · colloc-reviewer-v1

You are reviewing collocations for a learner's English–Chinese dictionary. Rules: C:/Users/greypapl/project/整理单词/prompts/colloc.md (read it first). {INPUT} has one collocation per line:

```
collocation | pattern | 中文 | headword[,headword]
```

Check every line. **Write to {OUTPUT} only the lines that need a change**:

1. A corrected full line (same collocation in field 1, all 4 fields) when the pattern code or the Chinese is wrong or unnatural. Keep the headword field as it is.
2. `collocation | delete:<reason>` when it should not be in the layer:
   - `free` — predictable; a learner would produce it correctly anyway (learn a language, correct answer, listen to the radio, horrible experience)
   - `wrong` — not idiomatic English, or the meaning is wrong
   - `phrase` — really an idiom, phrasal verb, prepositional phrase or fixed compound (belongs in the phrase layer)
   - `rare` — unusual or dated

Be firm with `free`: keep only combinations where the word choice is fixed by usage and a Chinese learner might choose a different word (make a mistake, heavy rain, strong coffee, highly likely, deeply regret, pay attention). Do not touch correct lines. Do not add new lines.

Field 1 must be copied exactly. After writing, run
`.venv/Scripts/python -X utf8 -I scripts/colloc.py review-check {NAME}` and fix every error. Reply with the check line and the number of edits/deletions.
