# 短语层 · phrase-compound-v1（复合词写手）

Line format: C:/Users/greypapl/project/整理单词/prompts/phrase-writer.md (same 5 fields; read only its "Output" section).

{INPUT} lists expressions that passed a first screening (one per line). For each, write one entry line with the correct type (`compound` for open compounds; `idiom`, `phrase` or `phrv` if that is what it is). Use the normal written form (keep the input spelling unless a capital is required). **Be strict:** write a line only if the Oxford Advanced Learner's Dictionary (or Longman / Cambridge) would list it as its own entry, idiom or phrasal verb. Leave out free combinations whose meaning is just the sum of the words (pork sausage, police patrol, pose a question, piece of furniture), technical terms, dated items, and anything you are not sure about — do not write a line for them. Expect to leave out about a third.

Write {OUTPUT} with the Write tool from your own knowledge, then run
`.venv/Scripts/python -X utf8 -I scripts/phrase.py check {NAME}` and fix every error. Reply with the check line only.
