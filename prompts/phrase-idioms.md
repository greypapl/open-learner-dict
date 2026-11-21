# 短语层 · phrase-idioms-v1（习语按主题）

Line format and inclusion rules: C:/Users/greypapl/project/整理单词/prompts/phrase-writer.md (same 5 fields; read only its "What to include" and "Output" sections).

{INPUT} lists themes (one per line). C:/Users/greypapl/project/整理单词/work/phrase/idioms-have.txt lists idioms the dictionary already has.

For each theme, list the idioms and fixed sayings (type `idiom`; proverbs too) that an English learner up to C1 would actually meet — the kind found in the Cambridge or Oxford idioms dictionaries — and that are **not already in idioms-have.txt**. Aim for 40–100 per theme; stop when you run out of genuinely common ones. Use the citation form (`sb`, `sth`, `one's`). No rare, archaic or regional-only idioms; no literal phrases.

Write {OUTPUT} with the Write tool from your own knowledge (several parts appended is fine), then run
`.venv/Scripts/python -X utf8 -I scripts/phrase.py check {NAME}` and fix every error. Reply with the check line only.
