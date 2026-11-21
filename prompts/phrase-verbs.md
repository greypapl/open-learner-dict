# 短语层 · phrase-verbs-v1（短语动词补全）

Line format and inclusion rules: C:/Users/greypapl/project/整理单词/prompts/phrase-writer.md (same 5 fields; read only its "What to include" and "Output" sections).

{INPUT} lists verbs (one per line). {HAVE} lists expressions the dictionary already has that start with these verbs.

For each verb, write the **phrasal verbs and prepositional verbs** (type `phrv`) that a learner's dictionary (Longman Phrasal Verbs Dictionary, Oxford Phrasal Verbs) lists and that are **not in {HAVE}**. Also add a fixed verb idiom only if it is very common (type `idiom`). Most verbs have 0–5 missing items; very common verbs (get, put, come, take, turn, break, bring, carry, hold, run, set…) may have 10–30. Do not pad: no literal combinations (walk into the room), no rare or archaic ones.

Write {OUTPUT} with the Write tool from your own knowledge, then run
`.venv/Scripts/python -X utf8 -I scripts/phrase.py check {NAME}` and fix every error. Reply with the check line only.
