# 例句层 · example-v1（写手）

For a learner's English–Chinese dictionary, write **one example sentence for every line** of {INPUT}. Each line is one sense of a frequent English word:

```
sense_id | word | pos | level | 中文释义 | en_short (English definition of this sense)
```

Lines of the same word are adjacent: read all senses of a word first, then write a sentence for each that shows **that sense and not another one**. The 中文释义 and en_short together define the sense; if they disagree slightly, follow en_short.

## Rules for the English sentence
- Like the examples in Oxford Learner's / Cambridge / Longman learner's dictionaries: natural, everyday, the kind of sentence a native speaker would actually say or write. Not a definition, not a textbook cliché (*This is a pen.*), not a quote.
- 6–14 words usually (4–22 allowed). One sentence.
- Difficulty follows `level`: A1–A2 words → short, simple sentences with only common words; B1–B2 → ordinary sentences; C1–C2 → may be more formal, but the other words should still be easier than the headword.
- The headword must appear, in any inflected form (*go → went, goes*; *child → children*). Use it **in the given part of speech** (n. sense → as a noun).
- Show typical usage: a common collocation or grammar pattern of this sense (*make a decision*, *interested in*, *depend on*) is better than a bare sentence.
- For function words (the, of, to, will…) show the sense's typical use clearly.
- For senses tagged with a register in en_short / 中文 (informal, offensive, old use), still write a sentence that shows the meaning neutrally; for offensive senses, write a sentence that describes or reports the word's use, not an insult aimed at someone.
- No real people's names, brands, companies or current events; use ordinary first names (Tom, Anna, my sister). No violence, sex, drugs or politics beyond what the sense itself needs; keep it suitable for school students where possible.

## Rules for the Chinese translation
- Natural, fluent 简体中文, the way a good dictionary translates its examples — translate the meaning, not word for word.
- The translation should make the sense visible (the Chinese for the headword should normally match one of the 中文释义 words or be a natural equivalent in context).
- Use full-width Chinese punctuation (，。？！), end with 。？or！. Numbers may stay as Arabic numerals. Keep names in English letters only if unavoidable; otherwise use common Chinese names (汤姆, 安娜).

## Output: {OUTPUT}

One line per input line, same order, 3 fields separated by ` | `:

```
sense_id | English sentence | 中文译文
w000097.1 | We went to the beach last weekend. | 上周末我们去了海边。
w000097.2 | It's getting late, so I'd better go. | 时间不早了，我该走了。
```

- Every sense_id of the input exactly once. No other text, no headings.

Write the file with the Write tool from your own knowledge (appending in several parts is fine), then run
`.venv/Scripts/python -X utf8 -I scripts/examples.py check {NAME}` and fix every error it reports (it checks fields, length, that the headword or an inflected form appears, and that no sense is missing). Reply with the final check line only.
