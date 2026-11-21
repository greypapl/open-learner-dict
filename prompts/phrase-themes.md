# 短语层 · phrase-themes-v1（类别横扫）

Line format and inclusion rules: C:/Users/greypapl/project/整理单词/prompts/phrase-writer.md (same 5 fields; read only its "What to include" and "Output" sections).

{INPUT} lists categories (one per line, with a few examples). For each category, list the fixed expressions of that kind (type `phrase`, `idiom`, `phrv` or `compound` as appropriate) that a learner up to C1 actually meets and that a learner's dictionary would list. Aim for 50–120 per category; stop when you run out of genuinely common ones. Use the citation form (`sb`, `sth`, `one's`).

The dictionary already has about 12,000 phrases; duplicates are removed automatically, so do not worry about them — but prefer the less obvious items over the first ones everyone thinks of. No free combinations, no rare/regional-only items, no proper names.

For delexical verb + noun collocations (take a break, make a mistake), include only ones in the household/daily-routine category, and only when they are fixed (do the dishes, make the bed).

Write {OUTPUT} with the Write tool from your own knowledge (several appended parts is fine), then run
`.venv/Scripts/python -X utf8 -I scripts/phrase.py check {NAME}` and fix every error. Reply with the check line only.
