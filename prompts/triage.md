# 尾部初筛 · triage-v1

You screen a list of very rare English headwords (one per line in {INPUT}) for a learner's English–Chinese dictionary that already has ~110,000 common words. Decide for each word whether it deserves a full dictionary entry.

**KEEP** a word only if it is an established English word that a mid-size general dictionary (Merriam-Webster Collegiate, Collins English Dictionary) would list as a headword AND at least one of these holds:
- an educated general reader could meet it in newspapers, novels, popular science, or school/university subjects;
- it is a well-established derivative or compound of a common word (`unthinkingly`, `overpraise`, `restorability` only if actually used);
- it is a core term of a major field that students learn (`actinometer`, `acotyledon`, `aldicarb` are borderline → keep only if you are confident it is a standard term).

**DROP** (do not list) everything else, in particular:
- chemical compound, drug, mineral, gene/protein names (`abietylamine`, `acetaldoxime`, `abelsonite`);
- taxonomic Latin names and rare species names;
- rare medical/anatomical jargon not found in general dictionaries (`abepithymia`, `acanthocheilonemiasis`);
- obsolete, archaic, dialect or nonce words (`aboon`, `accoy`), unless still known from literature (`absquatulate` keep);
- mechanical derivatives nobody uses (`abhorful`, `abominableness`, `aboundingly`);
- misspellings, proper nouns, non-English words.

When unsure, DROP. Expect to keep roughly 10–35% of a typical list.

## Output

Write {OUTPUT}: only the KEEP words, exactly as spelled in the input, one per line, in input order. The very last line must be `END <number of input lines>`. Nothing else (no notes, no codes).
Work through the input in order in chunks; do not skip any part of the list.
