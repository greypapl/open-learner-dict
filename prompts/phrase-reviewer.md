# 短语层 · phrase-reviewer-v1

You are reviewing phrase entries for a learner's English–Chinese dictionary. {INPUT} contains entries written by another model, one per line, in this format (rules: C:/Users/greypapl/project/整理单词/prompts/phrase-writer.md — read it first):

```
phrase | type | 义项 ; 义项 | 级别 | 标记
```

Check every line. **Write to {OUTPUT} only the lines that need a change**, in one of two forms:

1. A corrected full line (same phrase in field 1, all 5 fields), when something is wrong but the entry should stay:
   - wrong or misleading Chinese, wrong sense order (most common meaning first), missing a very common sense, a rare sense that should go;
   - wrong type, POS, level, tags, or missing `nokid`;
   - English definition wrong or uses the phrase itself.
2. `phrase | delete:<reason>` when the entry should not be in the dictionary. Reasons:
   - `free` — free combination; meaning is just the sum of its words (eat lunch, very good, big city)
   - `rare` — archaic or very rare expression a C1 learner would not meet
   - `proper` — a proper name (Persian Gulf, New York)
   - `wrong` — not a real English expression, or the meaning is invented
   - `variant` — a near-duplicate of another entry in the file (give the kept form in the line: `be used to | delete:variant=used to`)

Do not change lines just for style. Do not touch correct entries. Do not add new phrases. If nothing needs changing, write an empty file.

Field 1 must be copied exactly from the input line. After writing, run
`.venv/Scripts/python -X utf8 -I scripts/phrase.py check {NAME} --role reviewer`
and fix all errors. Reply with the check line and the number of edits/deletions.
