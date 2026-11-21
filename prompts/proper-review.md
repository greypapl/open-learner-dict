# 专名层审核 · proper-review-v1

You review the **proper-noun layer** of an open English–Chinese learner dictionary: names a learner meets in English text — people's given names and surnames, famous people, places, brands, organisations, abbreviations, works (books, films, TV shows, bands' songs…), peoples, religions and myths, events. Each name has a mainland Chinese name, a short Chinese note, and a Taiwan name. These were written by a model and never reviewed; an independent check found roughly 1 in 10 names needs a fix.

Input lines in {INPUT} (one name per line; names of the same entry are adjacent, `#1`, `#2`):

```
<p_id>#<i> | Display | type | 中文名 | 说明 | 台湾译名
```

type is one of: person place brand org abbr work people religion event other.

## What to fix
Check every line from your own knowledge. Typical problems:
- **Not the usual mainland name.** The 中文名 must be the name mainland readers actually know: the established name for famous people, places, brands and works (the official Chinese brand name, the mainland release title of a film or TV show, the 新华社 / 外国地名译名手册 / 世界人名翻译大辞典 form for places and people). If a famous person, place or brand has a well-established Chinese name and the line has a different transliteration, **change it** — even if the line's version is a defensible transliteration. Taiwan-style transliterations in the mainland field are wrong (put them in the Taiwan field). Watch for names of one language transliterated as if from another (Swedish -son, Turkish, Arabic, Japanese, German names).
- **Wrong person / thing.** The name is confused with a similar one (a god vs. a different god, Roman vs. Greek form, a band vs. its song).
- **Wrong type** (a band is `org`, not `work`; a mythological figure is `person`; a demonym or ethnic group is `people`).
- **Note too narrow or wrong.** For a given name or surname that many people have, the note should say so (英语男子名 / 英语姓氏 / 意大利姓氏), not name one famous bearer only. Notes that are out of date (a former president described as president) or wrong must be fixed. Keep notes short (≤ 20 characters).
- **Missing main sense.** If an entry lists only a minor sense and the main one a learner needs is missing, add it as a new name `#<count+1>` (an entry has at most 3 names).
- **Taiwan name.** When you change the 中文名, always give the matching Taiwan name too (台湾通行译名, in Traditional characters; often a different transliteration, e.g. 悉尼 → 雪梨, 贝克汉姆 → 貝克漢). Fix the Taiwan field also when only it is wrong.
- **Bad entry.** Delete only entries that are not proper names, are misspellings, or are a meaningless plural/possessive of another entry. Fix the display form when only capitalisation or punctuation is wrong (a missing apostrophe or final full stop).

How sure you need to be: **if you know the established name, fix it.** For an obscure person or place with no established Chinese name, a reasonable standard transliteration is fine — leave it. Do not change a correct name just because another spelling also exists, and do not rewrite correct notes for style.

## Output: {OUTPUT}
Write **only lines that need a change**, in one of these forms (fields separated by ` | `):

```
<p_id>#<i> | type | 中文名 | 说明 | 台湾译名      change this name (write all four fields, changed or not)
<p_id>#<i> | drop | reason                       remove this name (the entry keeps at least one)
<p_id> | display | New Display                   fix capitalisation / punctuation only
<p_id> | delete | reason                         remove the whole entry
```

Examples (invented for illustration):
```
p_sydney#1 | place | 悉尼 | 澳大利亚城市 | 雪梨
p_bjorkman#1 | person | 比约克曼 | 瑞典姓氏 | 比約克曼
p_bonos#1 | delete | plural of Bono, not a separate name
```
Names and Taiwan names: 1–16 characters, no brackets, no ；。|. Use `-` for an empty note.

Read every line yourself — do not use scripts to judge. Write the file with the Write tool (appending in parts is fine), then run `.venv/Scripts/python -X utf8 -I scripts/proper_review.py check {NAME}` and fix every ✗ error for your chunk. Reply with the check line for your chunk only.
