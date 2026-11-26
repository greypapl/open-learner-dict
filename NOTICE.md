# Third-party data

| Source | Used for | License |
|---|---|---|
| [ECDICT](https://github.com/skywind3000/ECDICT) | headword candidates, inflections (`exchange`), exam tags (`tag`) — **no definitions** | MIT |
| [wordfreq](https://github.com/rspeer/wordfreq) | frequency ranking | data: CC BY-SA 4.0 |
| [CMUdict](https://github.com/cmusphinx/cmudict) | US pronunciation, syllable stress | BSD-2-Clause |
| [OpenCC](https://github.com/BYVoid/OpenCC) | Simplified → Traditional character conversion (`s2tw`; Taiwan wording reviewed by model) | Apache-2.0 |

All definitions, English glosses, register labels, CEFR estimates, word families and affix analyses
are newly written and reviewed by large language models (primarily Claude models; proper-noun round-2 review includes Gemini 4 Neon; see each entry's `meta`).

# Licenses

- Data (`data/`, `work/merged/`, release files): Creative Commons Attribution-ShareAlike 4.0 International — see [LICENSE-DATA](LICENSE-DATA) / https://creativecommons.org/licenses/by-sa/4.0/
- Code (`scripts/`): MIT — see [LICENSE](LICENSE)
