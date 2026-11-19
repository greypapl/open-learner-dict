# 简释扩展层 · gloss-v1

For a learner's English–Chinese dictionary, write a very short Chinese gloss for each rare English word in {INPUT} (one word per line). These words were judged too rare for full entries; this layer only tells a reader roughly what the word means. It is published separately and marked as unreviewed, so **accuracy matters more than coverage: if you do not actually know the word, skip it.**

## Output: {OUTPUT}, exactly one line per input line, same order, same spelling

```
chabazite | n.菱沸石 [domain:矿业]
abhorful | adj.可憎的 [dated]
aboundingly | adv.丰富地, 大量地
cheechako | n.新来者, 新手 [us,informal]
percolater | skip:junk
sturnus | skip:not-english
```

- Format: `word | sense` or `word | sense ; sense` (at most 2 senses, most common first). Optional third field `| nokid` for offensive, sexual or drug words.
- A sense is `POS` immediately followed by Chinese, then optional ` [tag,tag]`.
  - POS only: `n.` `v.` `adj.` `adv.` `prep.` `conj.` `pron.` `det.` `int.` `num.` `abbr.`
  - Chinese: 1–3 expressions separated by `, `, each ≤ 12 characters; no sentences, no brackets （）(), no ；。
  - Tags only: `formal` `informal` `slang` `dated` `literary` `uk` `us` `offensive-mild` `offensive-strong` `domain:<领域>`, where 领域 is one of: 医学 解剖 药学 生物 植物 动物 化学 物理 数学 天文 地质 地理 气象 计算机 电子 机械 建筑 军事 航海 航空 法律 经济 金融 商业 政治 宗教 哲学 语言 文学 音乐 美术 体育 烹饪 农业 心理 教育 历史 摄影 纺织 印刷 矿业 统计 逻辑 神话. Technical words should carry a domain tag.
- Skip reasons (`word | skip:<reason>`): `junk` (misspelling, not a real word, or you cannot confirm it), `not-english` (Latin taxon names, unassimilated foreign words), `not-lemma` (pure inflected form), `proper-out-of-scope` (names, places, brands), `unknown` (real-looking word whose meaning you are not sure of).
- Derivatives: gloss from the base meaning (`aboundingly` → adv.丰富地). Chemical/mineral names: use the standard Chinese term if you know it (化合物 names may be transliterated as in Chinese chemistry); otherwise `skip:unknown`.
- Do not invent: a wrong gloss is worse than `skip:unknown`.
