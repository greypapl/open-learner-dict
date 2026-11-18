# 词条规范 · rules-v3（写手、审核、仲裁共用）

## 紧凑行格式（每个词头一行，字段用 ` | ` 分隔，共 10 个字段）

```
word | 义项 ; 义项 | 美音 | 英音 | 音节 | 词族 | 词缀 | 异体 | 级别 | 标记
happy | adj.快乐的, 高兴的, 幸福的 = feeling or showing pleasure | = | = | hap·py | happiness, unhappy, happily | - | - | A1 | -
coach | n.教练, 指导 = a person who trains a sportsperson or team ; v.训练, 指导, 辅导 = to train or teach someone ; n.长途汽车, 大客车 = a comfortable bus for long journeys [uk] | = | kəʊtʃ | = | coaching | - | - | A2 | -
went | skip:not-lemma
```

- **义项**：`词性`紧接中文，` = ` 后接英文简释，可选 ` [标签,标签]`；多个义项用 ` ; ` 分隔。
- **美音**：`=` 取输入 `ipa_us_cmu` 的第 1 个读音，`=2` 取第 2 个；CMU 为空或明显有误（重音错、双主重音 ˈ、单音节带重音符）时直接写音标。
- **英音**：RP 标准（ɒ əʊ ɑː 等）；与美音完全相同时写 `=`。
- 音标用宽式 IPA，重音符 ˈ ˌ 放音节首，不加斜杠；单音节词不加重音符。
- **音节**：拼写的音节切分，用 `·` 连接；与原词相同（单音节）写 `=`。
- **词族 / 词缀 / 异体**：`, ` 分隔，没有写 `-`。
- **标记**：`-`，或空格分隔的 `low`（没把握）、`nokid`（不宜儿童）、`mild` / `strong`（冒犯程度，自动视为不宜儿童）。
- 字段内不得出现 ` | `；英文简释内不得出现 ` ; ` 和 ` = `。

## 是否收录（skip）

`word | skip:<原因>`，原因只能是：
- `not-lemma`：纯屈折形式且无独立词义（went、children）；有独立词义的保留（left adj.、better、data）。
- `proper-out-of-scope`：专有名词，除 星期/月份/国家/语言/民族与国籍形容词/重大节日/常用称谓缩写（Mr, Dr）外，人名、城市、州、公司、品牌一律跳过。
- `abbr-rare`：非大众常用缩写（TV、USA、CEO、Co、Inc、Ltd 保留）。
- `junk`：拼写错误、无意义组合、无法确认是真实英文词。**拿不准时宁可 junk。**
- `not-english`：未被英语吸收的外语词。**拉丁学名（属名、种加词，如 sturnus、tamias、pectoris）一律 not-english**；只有已作英语普通名词通用的才收（如 amoeba、chlamydia、hippopotamus、rhododendron）。

## 释义规则（最重要）

1. 义项按**现代英语实际使用频率**从高到低排；第一个义项是学习者最先该学的意思。
2. 中文写 1–4 个近义表达，用 `, ` 分隔；每项 ≤12 字；不写长句、括号注释、例句，不用 ；。（）() 。
3. 每个词性最多 3 个义项，全词最多 6 个。宁少勿错，不写冷僻义。
4. 词性只能是 `n.` `v.` `adj.` `adv.` `prep.` `conj.` `pron.` `det.` `int.` `num.` `aux.` `abbr.`（不分 vt/vi，冠词用 det.）。
5. 英文简释 ≤12 个单词，不用被释义词本身作答。
6. 标签只能取：`formal` `informal` `slang` `dated` `literary` `uk` `us` `offensive-mild` `offensive-strong` `domain:<领域>`。只有专业义的罕见词必须标领域。领域只能是：
   医学 解剖 药学 生物 植物 动物 化学 物理 数学 天文 地质 地理 气象 计算机 电子 机械 建筑 军事 航海 航空 法律 经济 金融 商业 政治 宗教 哲学 语言 文学 音乐 美术 体育 烹饪 农业 心理 教育 历史 摄影 纺织 印刷 矿业 统计 逻辑 神话

## 其他字段

- **词族**：同词族中真实存在且常用的派生/复合词，最多 6 个；不同词源的词不算。**只收由本词派生或含本词词根的词**，不收同类词、近义词或配对词（pedicure 不收 manicure，tweeter 不收 woofer，monomer 不收 polymer，passcode 不收 password）。
- **音节**：拼写与词头完全一致，包括大小写（Lakota → La·ko·ta）。**每个读出的音节都要切开，复合词的组成部分也要细切**：o·ver·cook（不是 over·cook），pol·y·math，read·y-made，blotch·y，ed·it·a·ble。
- **词缀**：只拆标准、共时可辨的前后缀（`un-, -ness`）；词根不拆；拿不准写 `-`。
- **异体**：英美拼写或常见异体（colour → color）。**只收同一个词的不同拼写**，不收同义词或英美不同说法（undershirt 不收 vest，eggplant 不收 aubergine，tailpipe 不收 exhaust pipe）。
- **级别**：CEFR 估计 A1–C2；罕见专业词 C2。
- **nokid**：冒犯、色情、毒品、暴力血腥、强烈负面的词。
- **low**：对义项或排序没把握；罕见词、新词、不熟悉的词必须标 low。
