# 专名层 · proper-v1

For a learner's English–Chinese dictionary, give the standard Chinese name for each word in {INPUT} (one lowercase word per line, sorted by frequency). These are fairly frequent tokens in English text (wordfreq zipf ≥ 2) that the main dictionary does not cover; later chunks are rarer. Most are proper nouns: places, people's names, brands, organisations, abbreviations. The layer is published separately and marked unreviewed. **Accuracy matters more than coverage: if you are not sure, skip.**

## Output: {OUTPUT}, exactly one line per input line, same order, same spelling in field 1

```
chicago | Chicago | place:芝加哥=美国城市
jordan | Jordan | place:约旦=中东国家 ; person:乔丹=英语人名
james | James | person:詹姆斯=英语男子名
obama | Obama | person:奥巴马=美国前总统
google | Google | brand:谷歌=美国科技公司
fbi | FBI | abbr:联邦调查局=美国联邦执法机构
nato | NATO | org:北约=北大西洋公约组织
hamlet | Hamlet | work:哈姆雷特=莎士比亚悲剧 ; common
holmes | Holmes | work:福尔摩斯=侦探小说人物 ; person:霍姆斯=英语姓氏
angeles | skip:fragment
iphone | iPhone | brand:苹果手机
quran | Quran | religion:古兰经=伊斯兰教经典
mclaren | McLaren | brand:迈凯伦=英国汽车品牌
yeah | common | int.是的, 对
lol | common | abbr.哈哈, 笑死 [informal]
lmao | common | int.笑死了 [slang] | nokid
asdf | skip:junk
der | skip:not-english
```

### Proper names: `word | Display | type:中文[=说明] [; type:中文[=说明]]`
- **Display**: normal written form with correct capitals (`Chicago`, `FBI`, `iPhone`, `McLaren`, `eBay`).
- **type** only: `place` (countries, cities, regions, rivers, mountains, buildings) `person` (real or given names, surnames, famous people) `brand` (companies, products, games, apps) `org` (organisations, teams, parties, agencies) `abbr` (abbreviations of names/organisations, read as letters) `work` (books, films, TV shows, music groups) `people` (ethnic groups, tribes, nationalities not already in the dictionary) `religion` (gods, scriptures, religious terms) `event` (wars, holidays, historical events) `other`.
- **中文**: the standard Simplified Chinese name used in mainland China media (芝加哥, 奥巴马, 谷歌). Use the established translation; for common given names and surnames use the standard Xinhua transliteration (詹姆斯, 史密斯). Max 12 characters, no brackets.
- **说明** (optional, recommended when the name is ambiguous or not famous): ≤ 12 characters, e.g. `=美国城市` `=英语男子名` `=日本动漫`.
- At most 3 readings, most common first. If the word is also an ordinary English word that the dictionary should have, add `; common` as the last reading (e.g. `hamlet` above), but do not invent rare readings.
- Surnames that are also given names: one `person` reading is enough (`=英语姓氏` or `=英语人名`).

### Ordinary words: `word | common | <senses> [| nokid]`
Some inputs are ordinary words, interjections, slang or internet abbreviations the main dictionary missed. Gloss them like this: at most 2 senses separated by ` ; `, each `POS` immediately followed by 1–3 Chinese expressions (`, `-separated, each ≤ 12 characters), optional ` [tag,tag]`.
- POS: `n.` `v.` `adj.` `adv.` `prep.` `conj.` `pron.` `det.` `int.` `num.` `abbr.`
- tags: `formal` `informal` `slang` `dated` `literary` `uk` `us` `offensive-mild` `offensive-strong` `domain:<领域>` (领域: 医学 药学 生物 化学 物理 数学 计算机 电子 军事 法律 经济 金融 商业 政治 宗教 体育 音乐 文学 历史 地理 语言 烹饪 农业 心理 教育).
- `| nokid` at the end for offensive, sexual or drug words.

### Skip: `word | skip:<reason>`
- `junk` — typos, letter strings, tokenizer pieces (`th`, `ve`, `ll`), things you cannot identify.
- `not-english` — foreign words not used in English (`der`, `les`, `que`); but foreign *names* (Paris, Tokyo) are places.
- `fragment` — a piece of a multi-word name that is not used alone (`angeles`, `kong`, `zealand`, `san`, `los`).
- `numeral` — Roman numerals and number-like tokens (`xii`).
- `unknown` — looks like a name but you do not know what it refers to, or you do not know its standard Chinese form.

Do not invent Chinese names. A wrong name is worse than `skip:unknown`.
