# 短语层 · phrase-triage-v1（复合词初筛）

{INPUT} lists two- and three-word English expressions taken from an old dictionary (one per line). Most are technical terms or free combinations and must be dropped. Keep only expressions that deserve their own entry in a general learner's dictionary (Oxford Advanced Learner's / Longman / Cambridge):

- KEEP: everyday open compounds with a fixed meaning (credit card, big business, guinea pig, free trade, bus stop, ice age, water on the knee), common fixed phrases and idioms, common phrasal verbs.
- DROP: engineering/scientific/legal jargon (synchronous inverter, cumulative grid detector), free combinations whose meaning is just the sum of the words (open window, optimal estimate, travel allowance), fragments (upon this, request for), literal verb + adverb combinations (breathe freely, bind together, break apart, book a seat), plain spelling variants of solid words (book mark, breast bone), rare or dated items, proper names.

When unsure, drop. Expect to keep about 5–10%.

Write {OUTPUT} with the Write tool: only the kept expressions, copied exactly, one per line, in input order, and a last line `END <number of input lines>`. Do not use scripts to choose. Reply with "kept N".
