# 短语层 · phrase-supp-v1（补写）

Another writer already listed multi-word expressions for the headwords in {INPUT}; their output is {EXISTING}. That pass was too conservative and missed common expressions. Your job: **add only what is missing**.

Rules and line format: C:/Users/greypapl/project/整理单词/prompts/phrase-writer.md (read it first; same 5-field format, same inclusion rules).

Go through the headwords one by one. For each, think of the phrasal verbs, fixed phrases, idioms and open compounds that an Oxford/Longman/Cambridge learner's dictionary lists and that are **not already in {EXISTING}** (compare case-insensitively; also skip trivial variants of an existing entry). Typical gaps: phrasal verbs of very common verbs (get along, get over, get rid of, make up, make out, go off, go through, take over, take off…), everyday compounds (credit card, parking lot), and frequent fixed phrases (by the way, in case, at all).

Do not repeat existing entries. Do not pad with free combinations. Write the new lines to {OUTPUT} with the Write tool from your own knowledge (if nothing is missing, write an empty file), then run
`.venv/Scripts/python -X utf8 -I scripts/phrase.py check {NAME} --role supp`
and fix all errors. Reply with the check line.
