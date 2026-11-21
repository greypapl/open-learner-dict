# 短语层 · phrase-triage2-v1（复合词严筛）

{INPUT} lists multi-word expressions that passed a loose first screening (one per line). Many are still free combinations. Apply a strict test and keep an expression **only if the Oxford Advanced Learner's Dictionary (or Longman / Cambridge learner's dictionaries) would list it as its own entry, idiom or phrasal verb** — i.e. its meaning is not obvious from the words, or it is a fixed name for a common thing (credit card, pilot light, plum pudding, police dog, pig iron, plug up, piece by piece).

DROP anything whose meaning is just the sum of its parts (pork sausage, police patrol, police inspector, piece of furniture, pose a question, plant food, physical punishment, piano stool), technical/scientific terms (potassium chloride, pollen tube, positive charge, plane geometry), dated or rare items (picture palace, postpone without day), and plain spelling variants of solid words (pocket book, book mark).

When unsure, drop. Expect to keep roughly 40%.

Write {OUTPUT} with the Write tool: only the kept expressions, copied exactly, one per line, in input order, and a last line `END <number of input lines>`. Do not use scripts to choose. Reply with "NAME kept N".
