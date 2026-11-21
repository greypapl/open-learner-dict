# 质量抽检报告 · v0.9.0

由独立模型（Claude Fable）对发布版分层随机抽样逐条判断。抽样脚本 `scripts/audit.py`，判定规则 `prompts/audit.md`，
全部问题条目见 `work/audit/findings.jsonl`。**这是模型抽检，不是人工校对**；错误率是估计值，每层 100 条时误差约 ±5 个百分点。

- **major**：会误导使用者（释义错、词性错、主要义项缺失或排序明显不对、不该收录）。
- **minor**：不影响理解但不够好（音标小错、级别偏差、中文不自然、标签不准）。

| 层 | 抽样 | major | minor | major 率 | 有问题合计 | 主要问题类别 |
|---|---|---|---|---|---|---|
| core 1–2,000 | 100 | 0 | 6 | 0% | 6% | form 5、ipa 1 |
| core 2,001–10,000 | 100 | 0 | 3 | 0% | 3% | form 2、meaning 1 |
| core 10,001–30,000 | 100 | 0 | 6 | 0% | 6% | meaning 2、form 2、ipa 2 |
| core 30,001–60,000 | 100 | 0 | 3 | 0% | 3% | meaning 2、ipa 1 |
| core 60,001+ | 100 | 0 | 3 | 0% | 3% | form 2、meaning 1 |
| gloss | 100 | 2 | 5 | 2% | 7% | meaning 4、form 2、tag 1 |
| proper | 100 | 0 | 4 | 0% | 4% | zh 2、missing 1、form 1 |
| phrase | 100 | 0 | 7 | 0% | 7% | form 4、meaning 3 |
| collocation | 100 | 0 | 13 | 0% | 13% | tag 9、zh 2、meaning 1 |

主词典 500 条合计：major 0（0.0%），minor 21（4.2%）。

## 怎么读这些数字（维护者说明）

**不要把「major 0%」理解成没有错。** 这次抽检有三个局限：

1. **判得偏松。** 抽检员把「几个中文近义词里有一个是错的」都算 minor。按更严的口径（列出了错误的中文对应词就算 major），主词典 500 条里有 5 条应算 major，约 1%：
   - turnip 写了「萝卜」（应为芜菁）；qualitative 写了「质量的」（应为定性的）；cantata 写了「清唱剧」（那是 oratorio）；
   - seismographer 写了「地震学者」（那是 seismologist）；intrapersonal 写了「内省的」。
2. **抽检员不完全独立。** 主词典的仲裁也是 Fable 做的，同一个模型容易放过同一类错误。
3. **样本小。** 每层 100 条，一个错误就是 1 个百分点；音标是否逐个核对也无法确认。

所以比较稳妥的说法是：**主词典每 100 条约有 4–5 条值得改，其中约 1 条是释义用词错误**；常用词段（rank ≤ 10,000）没有发现释义错误。

## 这次发现的系统性问题

| 问题 | 例子 | 影响范围（估计） | 处理 |
|---|---|---|---|
| 词族里混进了相关但不同源的词 | start→startle、search→research、two→twelve、neutron→proton | 主词典约 2% | 待修：可让模型只重审 word_family 字段 |
| 词头本身是非标准写法 | living-room、come-down、freakshow、ngo（应为 NGO）、kw（应为 kW） | 主词典约 1% | 待修：来自候选词表，需要一轮「标准写法」检查 |
| 多词性词只给了一种重音 | perfect（动词重音在后） | 少数 | 结构限制：每个词只有一组音标 |
| 搭配层 pattern 把「形容词/名词 + 介词」记成 v+prep 或 n+n | resistant to、dedication to | 搭配层约 9% | 规则本身只有 6 种 pattern；下个版本拆出 adj+prep、n+prep、n+v |
| 短语层连字符写法 | runner up（应为 runner-up）、soft pedal | 短语层约 3% | 待修 |
| 简释层释义错误 | chariotee、grifolin | 简释层约 2% major | 该层未审核，已标 low |
| 专名译名不准 | Nilsson（尼尔松）、Rabindranath | 专名层约 2–4% | 该层未审核，已标 low |

## 结论

- 可以作为 v0.9（预览版）发布，前提是文档写明「模型生成、未经人工校对」和上面的问题清单。
- 发 v1.0 之前建议做完：词族重审、非标准词头检查、搭配 pattern 拆分，再换一个更严的口径重新抽检（样本加到每层 300 条）。
