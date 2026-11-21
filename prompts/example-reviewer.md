# 例句层 · example-v1（审核）

You review example sentences in a learner's English–Chinese dictionary. Each line of {INPUT}:

```
sense_id | word | pos | 中文释义 | en_short | English example | 中文译文
```

Check every line. A line is **wrong** if any of these holds:
1. The example does not show this sense (it shows another sense of the word, or the word is used in another part of speech).
2. The English is unnatural, ungrammatical, odd, or far harder than the headword's level.
3. The Chinese translation is inaccurate, misses part of the meaning, is unnatural Chinese, or renders the headword in a way that does not match this sense.
4. Content not fit for a school dictionary (unless the sense itself requires it), or a real person / brand / current event.

Do not rewrite lines that are merely acceptable; only fix real problems. Typical rate is a few lines per hundred.

## Output: {OUTPUT}

**Only the lines you change**, 3 fields separated by ` | ` — the full corrected sentence and translation (fix the translation alone if only that is wrong, but still give both fields):

```
sense_id | corrected English sentence | 修正后的中文译文
```

The headword (or an inflected form) must still appear; 4–22 words; English starts with a capital and ends with . ! or ?; Chinese ends with 。？or！. If nothing in the file needs changing, write an empty file.

Write the file with the Write tool, then run
`.venv/Scripts/python -X utf8 -I scripts/examples.py review-check {NAME}` and fix every ✗ error for {NAME}. Reply with the line for {NAME} only.
