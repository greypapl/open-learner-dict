# open-learner-dict 交接文档（STATUS）

> 更新于 2026-11-18。给 compact 之后的自己 / 维护者看：项目现状、怎么继续、踩过的坑。
> 设计依据见 [SPEC.md](SPEC.md)；逐步操作模板见 [prompts/RUNBOOK.md](prompts/RUNBOOK.md)。

## 1. 当前进度

| 阶段 | 状态 |
|---|---|
| 候选池构建 | ✅ 276,171 候选（主池 110,224 有 wordfreq 频率 + 尾部 165,947 来自旧 29 万词表） |
| Sonnet 初筛 | ✅ 92 片全部完成（`work/screen/S*.out.tsv`），合格 151,531 词 |
| 选词切批 | ✅ `work/selected.jsonl` → 758 批 `work/batches/B0001–B0758.input.jsonl`（每批 200） |
| Opus 写 / 审 / Fable 仲裁 | ✅ **B0001–B0453 全部合并**（`work/merged/`；B0089 起为 v3；B0343–B0453 为初筛后的尾部）。主体生产完成 |
| 已合并词条 | **86,851 条**（453/453 批），disputed 0；另有 61,076 个尾部词经初筛记为 too-rare（`work/merged/triage-skips.jsonl`） |
| 扩展层（例句、短语、同反义） | ⏳ 未开始 |
| 发布脚本（繁体、最终排名、CSV/SQLite/MDX/Anki、质量报告） | ⏳ 未写 |
| git | ✅ 2026-11-18 首次提交（work/raw、sources、headwords*.jsonl、selected.jsonl 不入库，见 .gitignore） |

批次顺序 = 选词顺序：B0001–B0306 ≈ 前 1000 + 主池（常用到中频），B0307 起为尾部罕见/专业词（几乎全是 K2）。

**自动推进已关闭**（无定时任务）。维护者说「跑 N 批」时由主会话按下面 §0 推进。

## 0. compact 后从这里继续（一轮 50 批的标准做法）

用户说「再跑 50 批 / 50 轮」= 下一段 50 个批次（例如 B0303–B0352）。

1. `get_usage` 看额度：5 小时窗口 ≥ 90% 或周额度 ≥ 95% 时不派新 agent。一轮 50 批 ≈ 窗口 35–41%、周额度 5%、Fable 1–2%，约 35–40 分钟。
2. `scripts/dispatch.py writer <15 批> --per 3 --effort low` 打标记 → 派 5 个 Opus 写手（Agent model=opus, effort=low）。
   提示词就是 dispatch.py 打印的内容（`writer()` 函数），每个写手 3 批。
3. 每收到一个 agent 完成通知：跑 `scripts/tick.py --upto <本轮末批>`（自动校验、算分歧、合并），按它的提示：
   - 「下一组写手」→ 在途写手 < 5 时再派（dispatch.py writer … --per 3 --effort low）
   - 「可派审核」→ `dispatch.py reviewer <5 批>` → 派 1 个 Opus 审核（默认强度）
   - 「可派仲裁」→ `dispatch.py arbiter <~10 批>` → 派 1 个 Fable 仲裁（model=fable）
4. 全部 merged 后：统计本轮（词条数、仲裁数、skip、额度变化），追加到 §3 末尾，更新 §1 进度行。
5. 主会话只看 agent 的一行回复和 tick 输出，**不读词条文件**。上下文过 60% 就提醒用户 compact。

B0307 起为尾部罕见/专业词，拉丁学名按 rules.md 一律 not-english。B0343 起是初筛后的尾部（大多应收录；真冷僻的用 skip:too-rare，不要标 junk）。

### 尾部初筛（triage，2026-11-19 起，用户选定「两个模型都筛、取并集」）

原尾部 B0343–B0758（83,131 词）先初筛，再把留下的词重切成新的 B0343+ 批次交给写手。
- 规则 `prompts/triage.md`；脚本 `scripts/triage.py`（make / check / rebatch）；数据在 `work/triage/`。
- 共 42 块，每块 2000 词。每块由 Sonnet 筛一遍写 `T<nnnn>.out.txt`，由 Opus（effort=low）筛一遍写 `X<nnnn>.out.txt`。最终保留两者并集。
- 每个 agent 筛 3 块，每个约 0.5% 的 5 小时额度。
- 进度用 `triage.py check` 看（显示还缺哪些块）。全部完成后跑 `triage.py rebatch`：
  - 原尾部输入移到 `work/batches/tail-raw/`；
  - 保留词切成新的 B0343…；
  - 去掉的词写入 `work/merged/triage-skips.jsonl`（skip:too-rare）。
- **已完成（2026-11-19）**：42 块全部筛完（T0032–34 的 Sonnet 结果过宽，已作废重筛，原结果保留为 *.lenient.txt）。并集保留 22,055 / 83,131（26.5%）。已经 rebatch 成 **B0343–B0453（111 批）**，原尾部 416 个输入移到 `work/batches/tail-raw/`，去掉的 61,076 词记在 `work/merged/triage-skips.jsonl`。初筛共用约 17% 的 5 小时额度。
- 跳过原因新增 `too-rare`（rules.md / validate.js 已加）。

## 2. 手动推进：每批的完整流程（v3，B0089 起）

工作目录 `C:/Users/greypapl/project/整理单词`，Python 一律 `.venv/Scripts/python -X utf8 -I`。
**v3 = 紧凑行格式**（规范 `prompts/rules.md`）：模型只写 `.txt` 紧凑行，`scripts/compact.py expand` 展开成原来的 JSONL，
validate / disputes / merge 照旧。旧提示词存档为 `prompts/*-v2.md`、`arbiter-v1.md`；B0001–B0088 是 v2，不返工。

**主会话保持精简**：只跑 status.py 和 dispatch.py、把打印出的提示词交给 Agent 工具；不要在主会话里读词条文件；上下文长了就 compact。

1. **看状态**：`.venv/Scripts/python -X utf8 -I scripts/status.py`
2. **写手**（Opus，每批一个）：`scripts/dispatch.py writer B0089 B0090 … [--effort low|medium]`
   → 打 `.started` 标记并打印每批的提示词（派 Agent 时把 effort 同样传给 Agent 工具）。写手自己跑 expand + validate，产出 `<B>.writer.txt` 和 `<B>.writer.jsonl`。
3. **审核**（Opus，**一个 agent 审 2 批**）：`scripts/dispatch.py reviewer B0089 B0090`
   → 审核只写有问题的条目到 `<B>.reviewer.txt`，自己 expand 成完整 `<B>.reviewer.jsonl` 并 validate。
4. **分歧**：`scripts/pipeline.py disputes <B>…` → `disputes.jsonl`（计数）+ `disputes.txt`（给仲裁的紧凑版）。0 条的直接第 6 步。
5. **仲裁**（Fable，**攒 10–15 批派一个**，约 40 条分歧）：`scripts/dispatch.py arbiter B0089 … B0100`（自动略过 0 分歧批次）。
6. **合并**：`scripts/pipeline.py merge <B>…` → `work/merged/<B>.jsonl` + `<B>.skips.jsonl`；meta 里按批次记录 prompt_ver 和写手 effort。

失败的 agent：删掉该阶段的 `.started`、`.txt`、part 文件后重派；`.started` 超过 120 分钟无产出也会被视为可重派。
**先检查是否其实已写完**：曾有 agent 写完输出后才因额度报错（B0013），expand + validate 通过就直接用。
只想看提示词不打标记：加 `--dry`。

## 3. 额度经验与分配

v2 实测（B0001–B0088）：
- 一批（写 + 审）≈ 5 小时窗口的 2–2.5%、周额度的 0.35–0.4%；写手 9–15 万 token，审核 9–10 万，仲裁 ~6 万/次（其中约 2/3 是读规范的固定开销）。
- 一个 5 小时窗口约 40 批；周额度约 250–280 批。并发：写手 ≤ 5、在途总数 ≤ 10。

v3 预期（**待 A/B 实测**）：写手输出体积降到 v2 的 ~38%（B0088 实测 80 KB → 31 KB），审核读入和输出都变小，仲裁输入减半。
分配：写手 1 批/agent（200 词，再大不省、风险升）；审核 2 批/agent；Fable 仲裁 10–15 批/agent。
Fable 较贵：**不再用 Fable 当写手**，除非周额度临近重置、余量会浪费。

### A/B 测试结果（2026-11-17，B0089–B0091，v3）

| | B0089 low | B0090 medium | B0091 默认 |
|---|---|---|---|
| 写手 token / 耗时 | 10.2 万 / 3.5 分 | 11.4 万 / 4.8 分 | 11.2 万 / 4.7 分 |
| 收录 / 跳过 | 193 / 7 | 197 / 3 | 199 / 1 |
| 平均义项数 | 1.37 | 1.37 | 1.46 |
| 审核 fix | 3（都是音标） | 1 | 2 |

- 审核：B0089+B0090 一个 agent 共 10.6 万 token / 70 秒；B0091 单批 9.9 万 / 59 秒 → **第二批几乎不增加 token**，固定开销占大头。
- Fable 仲裁 6 条（3 批）6.3 万 token / 28 秒，Fable 周额度未见变化（<1%）。
- 额度：3 批写+审共用 5 小时窗口约 5%（11%→16%），≈ **1.7%/批**（v2 为 2–2.5%）；周额度约 0.33%/批。百分比只有整数精度，属粗估。
- 抽查 low 版 10 条：义项、排序、音标都正常；low 的 3 个 fix 都是音标（单音节重音符、CMU 错音、次重音），不是释义问题。

**结论**：写手今后用 `--effort low`（Agent effort=low）。若某批审核 fix > 6 条或出现释义类错误增多，改回 medium。
审核可以一次审 3–4 批（第二批几乎免费）；写手每 agent 2 批也值得一试（固定开销同样很大）。

### 分组测试（2026-11-17，B0092–B0102，全部 low）

| 组织方式 | agent 数 | 每 agent token / 耗时 | 折合每批 token |
|---|---|---|---|
| 写手 1 批 | 3（B0089–91） | 10–11 万 / 3.5–4.8 分 | ~10.5 万 |
| 写手 2 批 | 4 | 12.7–13.7 万 / 4.5–5.8 分 | ~6.5 万 |
| 写手 3 批 | 1 | 13.0 万 / 8.4 分 | ~4.3 万 |
| 审核 1 批 / 2 批 | 1 / 1 | 9.9 万 / 10.6 万 | 9.9 / 5.3 万 |
| 审核 5 批 | 2 | 16.7–17.6 万 / 2.3–2.6 分 | ~3.4 万 |
| Fable 仲裁 10 批（39 条） | 1 | 7.3 万 / 49 秒 | — |

- 额度：本轮写 11 批 + 审 10 批 + 仲裁 10 批，5 小时窗口 18%→27%（含主会话自身开销），≈ **0.85%/批**；
  单批写手方案约 1.7%/批，v2 约 2–2.5%/批。Fable 周额度 +1%。
- 质量：5 批审核里后面的批次没有变松（每批 fix 1–8 条，和 v2 基线一致）；fix 多为词族混入同类词（manicure、woofer）和音标，
  已在 rules.md 补充「词族只收本词派生词」「音节大小写与词头一致」。释义类错误只 1 处（etcetera 词性）。

**最佳方案（今后照此）**：
- 写手：**每 agent 3 批**，`dispatch.py writer … --per 3 --effort low`（Agent effort=low）；同时在途 ≤ 5 个写手（一波 15 批，约 9 分钟）。
- 审核：**每 agent 5 批**，`dispatch.py reviewer <5 批>`，Opus 默认强度。
- 仲裁：**每 agent 约 10 批**，`dispatch.py arbiter <10 批>`，Fable。
- 预期：一个 5 小时窗口 ≈ 90–100 批；剩余 ~656 批 ≈ 7 个窗口。

### 50 批实跑（2026-11-18，B0103–B0152 + 补审 B0102，按「最佳方案」）

- 用时约 40 分钟（写手 17 个，≤5 并发；审核 10 个；Fable 仲裁 5 个）。
- 额度：5 小时窗口 7%→47%（含主会话开销）≈ **0.8%/批**；周额度 22%→27% ≈ 0.1%/批；Fable 14%→15%。
- 产出：10,030 条词条，222 条经仲裁，170 个 skip，0 条 disputed（另有 1 条仲裁删义项标 low）。
- 推算：一个 5 小时窗口约 **100 批**；剩余 606 批约 6–7 个窗口，周额度约需 60%。
- 本轮发现并已处理：
  - 写手偶尔把标签写成 `[a] [b]` 两组 → compact.py 已支持多组；validate.js 新增「en_short 含方括号」检查。
  - 词族混入同类/配对词、异体写成同义词、音节切太粗（over·cook）→ rules.md 已逐条补充规则与反例。
  - 审核把「英音写出与美音相同而没写 =」当问题 → reviewer.md 已注明等价写法不算问题（展开时本来也自动视为 ok）。

### 第二轮 50 批（2026-11-18，B0153–B0202）

- 用时约 35 分钟；5 小时窗口约 33%（跨窗口重置，约 0.65%/批）；周额度 29%→34%（0.1%/批）；Fable 15%→16%。
- 产出 9,765 条，155 条经仲裁，235 个 skip，0 条 disputed。累计 **39,718 条**。
- 新工具 `scripts/tick.py --upto <末批>`：一条命令完成校验、算分歧、合并，并提示下一步可派的写手/审核/仲裁组；
  `dispatch.py reviewer` 会写 `<B>.reviewer.group`，tick 等整组审核都产出后才算分歧。

### 第三轮 50 批（2026-11-18，B0203–B0252）

- 用时约 37 分钟；5 小时窗口 28%→67%（≈0.78%/批）；周额度 34%→39%；Fable 16%→18%。
- 产出 9,790 条，147 条经仲裁，210 个 skip，0 条 disputed。累计 **49,508 条**（252/758 批）。
- 审核最常修：异体填同义词、词族放配对词、CMU 美音错；释义类错误个位数（greaseball 释义、chitlins）。

### 第四轮 50 批（2026-11-18，B0253–B0302）

- 5 小时窗口 5%→46%（≈0.82%/批）；周额度 40%→45%；Fable 18%→19%。
- 产出 9,793 条，147 条经仲裁，207 个 skip，0 条 disputed。累计 **59,301 条**（302/758 批）。
- rules.md 新增：拉丁学名一律 not-english（已作英语普通名词的除外）。
- 已知：写手很少给罕见词标 low → 发布脚本按 zipf 自动补 low，无需返工。

### 第五轮 40 批（2026-11-18，B0303–B0342）

- 5 小时窗口 47%→73%（≈0.65%/批）；周额度 45%→49%；Fable 19%→20%。
- 产出 5,737 条，99 条经仲裁，2,263 个 skip（junk 2,142），0 条 disputed。累计 **65,038 条**（342/758 批）。
- **B0318 起输入换成旧 29 万词表的尾部**：按字母排序、无频率数据，几乎全是极冷僻的化学/矿物/医学词（abietylamine、acetaldoxime）。
  - 各写手对 junk 的尺度差异很大：同类批次有的保留 40–60 条，有的保留 180–198 条（B0321–B0323、B0339–B0342）。
  - 审核每批会把十几个被错判 junk 的真词捞回来，但不会全部复查。
  - **继续推尾部（B0343–B0758，约 416 批）之前，要先定统一标准**（见 §6）。

### 第六轮：尾部 111 批（2026-11-19，B0343–B0453，自动运行）

- 5 小时窗口 1%→88%（≈0.8%/批，含补写）；周额度 52%→63%；Fable 20%→23%。约 3 小时。
- 产出 21,813 条，532 条经仲裁，242 个 skip（too-rare 150、not-lemma 51、not-english 24、junk 17），0 条 disputed。累计 **86,851 条**（453/453 批）。
- 问题与处理：
  - 前 15 批（B0343–B0357）写手仍按旧标准大量跳过（保留 27–62%），等于又筛了一轮。处理办法：
    - 新写手提示附 `work/tmp/tailnote.txt`（存档：`prompts/tail-note.md`）：默认收录，只有 Collins/韦氏大学词典都不收的词才标 too-rare；
    - 对已写的 15 批另派「补写」agent，把错跳的词补成完整词条。
  - 补写后每批保留 185–200 条，与初筛结果一致。
  - 审核最常修：异体填成同义词或不同后缀形式、词族放配对词、英音照抄美音。tailnote 后来补了这几条字段提醒。
  - 仲裁中需要人工留意的：gonimeter 判为 goniometer 的误拼（skip:junk）；peevy 去掉无法确认的形容词义。

## 4. 质量情况

- 平均每批审核 fix 2–6 条，绝大多数是 word_family 混入无关词 / affixes 拆分牵强 / 音标重音；偶尔抓到真错（GDP≠GNP、plug≠插座、Lt≠上尉）。
- Fable 仲裁绝大多数采纳审核意见；至今 0 条 disputed。
- 抽查（B0001–B0005、50 批节点 30 条）未发现系统性问题。

## 5. 已做过的规则调整（都已写进提示词）

- writer-v2 / reviewer-v2：领域标签只能取固定 44 项（`domain:医学` 等，validate.js 会拦截）；CMU 读音明显错可改并标 `ipa_source:model`；单音节不加重音符；validate 拦截双主重音。
- reviewer：**音节切分点只要读得通就不改**（B0066 曾因此 17/19 条无谓分歧）。
- 所有模板：子 agent 的辅助脚本只能放 `<scratchpad>\<B>\` 自己的子目录（共享 scratchpad 曾互相覆盖）。
- B0011–B0014 曾派 Fable 写手；B0011、B0012 因 Fable 额度耗尽失败后改由 Opus 重写；B0013、B0014 保留 Fable 版本（有 `.writer.model` 标记，merge 会写入 meta）。

## 6. 已知问题（发布前处理，无需返工）

- **尾部（B0318–B0758）收录尺度不一** → 已决定：两个模型初筛、取并集（见 §0「尾部初筛」）。下面是当时的记录：
  - 旧 29 万词表字母序尾部，写手对 junk 的判断从 20% 到 80% 不等；被 skip 的大多是真实但极冷僻的专业词，并不是乱码。
  - 可选方案：
    - 明确规则：真词但无学习价值的用新 skip 原因（如 `too-rare`），只收派生词和有通用意义的词；
    - 先用脚本预筛（与已收词条同根的派生词、在其他词表中出现过的词），再派写手；
    - 主体到 B0317 为止，尾部改为扩展层，或者不做。
  - B0318–B0342 已合并的部分保持现状，统一标准后可按 skip 原因复查。
- 罕见词 `low` 标记普遍缺失：发布时对 zipf 低于阈值（或尾部批次）的词条统一补 confidence=low。

- 同形异音词（slaver 奴隶贩子 /ˈsleɪvə/ vs 流口水 /ˈslævə/、tarry）：每词条只有一套音标，目前只保留较常用的读音和义项；发布前考虑拆成同形异音的多个词条。

- 连字符词（easy-going、phone-in）的 wordfreq 频率偏高，挤进前 1000；最终排名需降权。
- 连字符词 syllables 有时未切分，发布脚本按连字符分段处理。
- 合并结果里 `rank` 为 null（`freq_rank_raw` 是原排名），最终排名等全部完成后按 skip 剔除重排。
- `zh_hant` 字段为 null，待 OpenCC（s2twp）批量填充（需安装 opencc，属下载，需确认）。
- 前 2 万词早期批次用的是 v1 规则吗？——否：试点 P0001–P0005 是 v1，正式批次 B* 全部是 v2；试点产物在 `work/merged/P*.jsonl`，发布时**不要**合进去（B 批次已覆盖这些词）。

## 7. 下一步建议

0. ✅ A/B 与分组测试已完成（见 §3 末「最佳方案」）：写手 3 批/agent + low，审核 5 批/agent，仲裁 10 批/agent。
1. 先 `git add` + 提交一次（`.gitignore` 已排除 sources/、work/raw/、.venv/）。
2. 继续 B0089 起的批次。
3. 主池（≈B0306）完成后：写发布脚本（最终排名、繁体、CSV/SQLite/JSON、JSON Schema），出一版质量报告（Fable 独立抽检 500 条）。
4. 再推尾部 B0307–B0758，然后扩展层。
