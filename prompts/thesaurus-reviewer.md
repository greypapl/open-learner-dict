# 同义词 / 反义词 · thesaurus-v1（审核）

You review synonyms and antonyms in a learner's English–Chinese dictionary. Each line of {INPUT}:

```
sense_id | word | pos | 中文释义 | en_short | synonyms | antonyms
```

`-` means empty. A line is **wrong** if:
1. A synonym does not fit **this sense** (it belongs to another sense of the word), has a different part of speech, or is only loosely related (hypernym, associated word: *animal* for *dog*, *walk* for *run*).
2. An antonym is not a real opposite of this sense, or has a different part of speech.
3. A very obvious, common synonym or antonym is missing (e.g. *big* with no *small*), or the list is padded with rare or odd words when common ones exist.
4. Register clash: slang offered for a formal word or vice versa when better options exist.

Do not rewrite lines that are merely acceptable, and do not add items to lines that are fine. Empty fields are correct for function words, concrete nouns without real synonyms and technical terms.

## Output: {OUTPUT}

**Only the lines you change**, 3 fields: `sense_id | synonyms | antonyms` — the full corrected lists (`-` for empty, `, ` between items, up to 4 synonyms and 2 antonyms). Every item must exist in the dictionary; the checker will tell you if one does not. If nothing needs changing, write an empty file.

Write the file with the Write tool, then run
`.venv/Scripts/python -X utf8 -I scripts/thesaurus.py review-check {NAME}` and fix every ✗ error for {NAME}. Reply with the line for {NAME} only.
