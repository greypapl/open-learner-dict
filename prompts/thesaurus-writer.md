# 同义词 / 反义词 · thesaurus-v1（写手）

For a learner's English–Chinese dictionary, give **synonyms and antonyms for every line** of {INPUT}. Each line is one sense of a common English word:

```
sense_id | word | pos | level | 中文释义 | en_short (English definition of this sense)
```

Lines of the same word are adjacent: read all senses of a word first, then answer **for this sense only** (e.g. *bright* "full of light" → light, brilliant / dark, dim; *bright* "intelligent" → clever, smart / stupid, dull).

## Rules
- **Synonyms**: 0–4 words or phrases that a learner could use **instead of the headword in this sense**, same part of speech, close in meaning. Prefer common words a learner would know or want to learn; put the closest/most common first. Phrasal verbs and fixed phrases are fine (*postpone* → put off, delay).
- **Antonyms**: 0–2 clear opposites for this sense, same part of speech. Only real opposites (*hot* → cold; *buy* → sell). Do not invent opposites with *not* or *un-* unless that word is standard (*happy* → unhappy, sad is fine).
- **Leave it empty** when there is no good answer — function words (the, of, to), most numbers, names of things (*table*, *giraffe* have no synonyms worth teaching), technical terms. Empty is better than a weak or loose match. Expect many lines to have no antonym. Pronouns, determiners and auxiliaries get no antonyms (*her* → him, *my* → your are not antonyms).
- Words differing in degree are fine (*huge* → enormous, vast, big). Merely related words are **not** synonyms: *walk* is not a synonym of *run*, *kitten* not of *cat*, and hypernyms (*animal* for *dog*) never count.
- Match register roughly: do not give slang for a formal word or vice versa, unless nothing else exists.
- Write each item in its normal dictionary form (lowercase unless it is always capitalised). Never list the headword itself.
- Every item must be a word or phrase that exists in this dictionary; the checker will tell you if one does not — then choose another common word or drop it.

## Output: {OUTPUT}

One line per input line, same order, 3 fields separated by ` | `; use `-` for an empty field and `, ` between items:

```
sense_id | synonyms | antonyms
w000123.1 | clever, intelligent, smart | stupid
w000124.1 | - | -
w000125.2 | put off, delay | -
```

Write the file with the Write tool (appending in parts is fine), then run
`.venv/Scripts/python -X utf8 -I scripts/thesaurus.py check {NAME}` and fix every ✗ error. Reply with the final check line only.
