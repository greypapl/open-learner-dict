# 定向修正 · fixes-v1

Four small clean-up passes over an English–Chinese learner's dictionary. Each input file is one kind; recognise it by its file name prefix. **Write to the output file only the lines that need a change** (an empty file is fine). Copy the key (the part before the separator) exactly. Judge from your own knowledge; do not use scripts to decide.

## H — headword spelling (`word | first sense`)
The headword list may contain nonstandard citation forms. Output `word | standard:<form>` only when the standard dictionary form (Oxford / Merriam-Webster / Collins) is different:
- written as two words: `living-room | standard:living room`, `freakshow | standard:freak show`
- written solid: `come-down | standard:comedown`
- capitalisation of abbreviations and names: `ngo | standard:NGO`, `kw | standard:kW`
Leave everything else out: correct solid compounds (airport, network, everyone), correct hyphenated words (would-be, so-so), and words where both spellings are standard (healthcare / health care, anymore, percent). When unsure, leave it out.

## Y — phrase citation form (`phrase | type`)
Output only for phrases whose written form is wrong:
- `phrase | fix:<form>` — wrong citation form but still a multi-word expression: missing object slot (`take up on | fix:take sb up on sth`), wrong article or spelling, a hyphen that belongs between only some of the words.
- `phrase | solid:<word>` — the standard spelling is a single solid or hyphenated word, so it is not a phrase: `runner up | solid:runner-up`, `play list | solid:playlist`, `soft pedal | solid:soft-pedal`.
Do not touch phrases that are fine; do not judge whether a phrase deserves to be in the dictionary.

## C — collocation pattern (`collocation | pattern`)
The original pattern set was too coarse. Output `collocation | <pattern>` only where the pattern is wrong. Allowed: `v+n` `adj+n` `n+n` `adv+adj` `v+adv` `adv+v` `v+prep` `adj+prep` `n+prep` `n+v`.
- `resistant to sth`, `associated with sth`, `torn between sth and sth` → `adj+prep`
- `dedication to sth`, `reason for sth`, `an observation about sth`, `nomination for sth` → `n+prep`
- `a pattern emerges`, `prices rise` → `n+v`
- `strongly recommend`, `deeply regret` (adverb first) → `adv+v`; `fall sharply` stays `v+adv`
- `depend on sth`, `listen to sth` stay `v+prep`; `a round of applause`, `traffic jam` stay `n+n`

## F — word family (`word: a, b, c`)
The family should list only words **derived from the headword or sharing its root** (happy: happiness, unhappy, happily). Remove members that are merely related in meaning, look similar, or are separate lexemes:
`start: startle` ✗, `search: research` ✗, `two: twelve, twenty, twin` ✗, `neutron: proton, electron` ✗, `guacamole: avocado` ✗.
Output `word: <remaining members>` (or `word: -` if none remain) only for lines where something is removed. Never add members. Compounds that contain the headword (bookshop for book) are fine. When unsure, leave the line out.

## After writing
Run `.venv/Scripts/python -X utf8 -I scripts/fixes.py check` and fix format problems in your own files (ignore other files and "未完成"). Reply with the number of lines you wrote per file.
