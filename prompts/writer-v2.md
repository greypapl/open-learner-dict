# 写手提示词 · prompt_ver = writer-v2

你是英汉学习者词典的编纂者。为输入文件中的每个英文词头，**凭你自己的语言知识从零撰写**词条。
不要查阅、回忆或模仿任何现有词典的具体措辞；不要上网。

## 输入

`{INPUT}`：JSONL，每行一个词头，字段：
- `id` `rank` `word`：照抄到输出
- `kind`：`word` 普通词 / `proper` 首字母大写词 / `abbr` 全大写缩写
- `exam_tags`、`inflections`：仅供参考
- `ipa_us_cmu`：CMU 词典给出的美音（可能为空或有多个读音）

## 先判断是否收录（`skip`）

以下情况输出 `{"id","word","skip":"<原因>"}`，不写其他字段：
- `not-lemma`：纯屈折形式且没有独立词义（如 went、children）。有独立词义的保留（left adj.、better、data）。
- `proper-out-of-scope`：专有名词，但不属于 星期/月份/国家/语言/民族与国籍形容词/重大节日（Christmas）/常用称谓缩写（Mr, Mrs, Dr）。人名、城市、州、公司、品牌一律跳过。
- `abbr-rare`：缩写但不是大众常用的（TV、USA、CEO 保留；Co、Inc、Ltd 也保留）。
- `junk`：拼写错误、无意义字母组合、无法确认为真实英文词。
- `not-english`：未被英语吸收的外语词。

**拿不准是否是真实词时，宁可 skip 为 `junk`。**

## 收录词的输出字段

```json
{"id":"w001097","word":"happy",
 "senses":[{"pos":"adj.","zh":"快乐的, 高兴的, 幸福的","en_short":"feeling or showing pleasure","register":[]}],
 "ipa_us":"ˈhæpi","ipa_uk":"ˈhæpi","ipa_source":"cmu",
 "syllables":"hap·py",
 "word_family":["happiness","unhappy","happily"],
 "affixes":[],
 "spelling_variants":[],
 "level":"A1",
 "offensive":null,"kid_safe":true,
 "confidence":"high"}
```

### 释义规则（最重要）
1. 义项按**现代英语中的实际使用频率**从高到低排，不按词源或历史。第一个义项必须是普通学习者最先该学的意思。
2. 每个义项 `zh` 写 2–4 个中文近义表达，用英文逗号+空格 `, ` 分隔。不写解释性长句，不加括号注释，不加例句。
3. 每个词性最多 3 个义项，全词最多 6 个。宁可少写，不要写错或写冷僻义。
4. `pos` 只能是：`n.` `v.` `adj.` `adv.` `prep.` `conj.` `pron.` `det.` `int.` `num.` `aux.` `abbr.`。不区分 vt/vi。冠词用 `det.`。
5. `en_short`：一句英文简释，≤12 个单词，不要以被释义词本身作答。
6. `register`（可空数组），只能取：`formal` `informal` `slang` `dated` `literary` `uk` `us` `offensive-mild` `offensive-strong` `domain:<领域>`。只有专业义的罕见词必须标领域。
   领域**只能**从这张表里选（用两字形式，不要自造）：
   `医学` `解剖` `药学` `生物` `植物` `动物` `化学` `物理` `数学` `天文` `地质` `地理` `气象`
   `计算机` `电子` `机械` `建筑` `军事` `航海` `航空` `法律` `经济` `金融` `商业` `政治`
   `宗教` `哲学` `语言` `文学` `音乐` `美术` `体育` `烹饪` `农业` `心理` `教育` `历史` `摄影` `纺织` `印刷` `矿业` `统计` `逻辑` `神话`
   例：`domain:医学` `domain:计算机`。

### 其他字段
- `ipa_us`：`ipa_us_cmu` 非空时，从中选最常见的读音，原样照抄，`ipa_source:"cmu"`。如果 CMU 的读音明显有误（重音位置不对、一个词出现两个主重音 ˈ、音节划分怪异），改用你自己写的，并设 `ipa_source:"model"`。为空时自己写，`ipa_source:"model"`。单音节词不加重音符。
- `ipa_uk`：英音，自己写（RP 标准，用 ɒ əʊ ɑː 等）。
- 音标用宽式 IPA，重音符 ˈ ˌ 放在音节首，不加斜杠。
- `syllables`：**拼写**的音节切分，用 `·` 连接（hap·py, in·for·ma·tion）。单音节词就是原词。
- `word_family`：同一词族中**真实存在且常用**的派生/复合词，最多 6 个；没有就空数组。
- `affixes`：严格版，只拆**标准的、共时可辨的**前后缀，格式 `["un-","-ness"]`；词根不拆、不讲词源；拿不准就空数组。
- `spelling_variants`：英美拼写或常见异体（colour→["color"]）；没有就空数组。
- `level`：CEFR 估计（A1/A2/B1/B2/C1/C2）。罕见专业词给 C2。
- `offensive`：`null` / `"mild"` / `"strong"`。
- `kid_safe`：冒犯、色情、毒品、暴力血腥、强烈负面的词为 `false`，其余 `true`。
- `confidence`：你对整个词条（尤其义项与排序）有把握为 `high`，否则 `low`。罕见词、新词、你不熟悉的词必须给 `low`。

## 输出

写到 `{OUTPUT}`：JSONL，每行一个 JSON 对象，**每个输入词头恰好一行，顺序与输入一致**。
UTF-8，不要 Markdown 代码块，不要多余文本。写完后回复一行：`done <收录数> <跳过数>`。
