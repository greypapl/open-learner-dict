# open-learner-dict 交接文档（STATUS）

> 更新于 2026-11-26。给 compact 之后的自己 / 维护者看：项目现状、怎么继续、踩过的坑。
> 设计依据见 [SPEC.md](SPEC.md)；逐步操作模板见 [prompts/RUNBOOK.md](prompts/RUNBOOK.md)。

## 1. 当前进度

| 阶段 | 状态 |
|---|---|
| 候选池构建 | ✅ 276,171 候选（主池 110,224 有 wordfreq 频率 + 尾部 165,947 来自旧 29 万词表） |
| Sonnet 初筛 | ✅ 92 片全部完成（`work/screen/S*.out.tsv`），合格 151,531 词 |
| 选词切批 | ✅ `work/selected.jsonl` → 758 批 `work/batches/B0001–B0758.input.jsonl`（每批 200） |
| Opus 写 / 审 / Fable 仲裁 | ✅ **B0001–B0453 全部合并**（`work/merged/`；B0089 起为 v3；B0343–B0453 为初筛后的尾部）。主体生产完成 |
| 已合并词条 | **86,851 条**（453/453 批），disputed 0；另有 61,076 个尾部词经初筛记为 too-rare（`work/merged/triage-skips.jsonl`） |
| 简释扩展层 | ✅ **48,359 条**（含 Opus 重试 2,692 条）（`work/merged/gloss.jsonl`，confidence=low，未审核） |
| 变形索引 | ✅ **43,970 个形式**（`work/merged/inflections.jsonl`，纯脚本） |
| 专名层 | ✅ **12,928 条**（经两轮审核：v1 Opus + v2 Fable/Gemini 4 Neon，confidence=medium；见 §0「专名层第二轮审核完成」） |
| 短语层 | ✅ **13,153 条**（`phrases.jsonl`，全部经 Opus 审核并做过连写定向修正，confidence=medium；见 §0 短语层各轮） |
| 搭配层 | ✅ **5,016 条**（`collocations.jsonl`，前 5,000 实词，Sonnet 写 + Opus 审，confidence=medium） |
| 扩展层（例句、同反义） | ✅ 已完成（见下方例句与同义/反义词两行） |
| 发布脚本 | ✅ `scripts/release.py --version 0.10.0` → `release/0.10.0/`（JSONL、CSV、SQLite 73.2MB、词表、MANIFEST），Schema 校验全过；`docs/DATA.md`、`schema/`、README 已同步。MDX、Anki 未做 |
| 例句 | ✅ 前 1 万词 + 全部 A1–C1 词，每个义项 1 句（29,034 条，Opus 写 + Opus 审），见 §0「例句层 v1 完成」。短语层例句未做 |
| 质量抽检 | ✅ v0.10.0：Fable 按更严口径（audit-v2）抽 2,100 条，含例句和繁体，报告 `reports/quality-0.10.0.md`；v0.9.0 的旧报告保留。例句繁体已在抽检后由 Sonnet 逐句校对（改 1,604 句，X01–X12，`hant.py make-ex`）。 |
| 同义 / 反义词 | ✅ 完成（2026-11-21）：`scripts/thesaurus.py`（make/check/review-make/review-check/apply，增量），prompts `thesaurus-writer.md` / `thesaurus-reviewer.md`。范围同例句（前 1 万 + A1–C1，28,912 个义项），每项必须是词典已有词条或短语。Opus low 写 73 块 × 400（约 24% 窗口），Opus 审 12 块 × 2,500，改 361 条；apply 时按规则去掉代词/限定词的人称、物主、指示词反义（he→she 这类，15 条）。结果：同义 46,954 条、反义 9,421 条。发布：`senses[].synonyms/antonyms`、`csv/relations.csv`、SQLite `sense_relations` |
| 简释层审核 | ✅ 完成（2026-11-21）：`scripts/gloss_review.py` + `prompts/gloss-review.md`，Opus 逐条审 51,159 个义项（G001–G026，每块 2,000），只输出要改/要删的行。试点 G002 改 29 条（1.5%）。**复数等变形不删**（试点删了 7 个拉丁复数，已撤回并改了规则）。26 块全部审完：改 423 条、删 14 个拼写错误词头（glossapharyngeal、irridentism 等），每块约 0.7% 的 5 小时窗口。**召回率低**：抽检查出的 12 条错误里，审核只改到 7 条，而且恰好都是 prompt 里举过的例子；另外 5 条（intertill、mezerein、packless、parapsis、torfaceous）是我按抽检结论手工追加到 reviewer.txt 的。所以 gloss 标 reviewed=true，confidence 仍为 low。想再提高只能换模型（Fable）再审一轮，或不给「不确定就别改」的限制。 |
| git | ✅ 2026-11-18 首次提交；2026-11-26 已公开推送至 `https://github.com/greypapl/open-learner-dict` 并发布 GitHub Release `v0.10.0` |

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

### 简释扩展层（gloss，2026-11-19 起，用户选定）

给初筛去掉的 61,076 个 too-rare 词各写一行中文简释，单独成层（不审核、不仲裁，统一 confidence=low）。
- 规则 `prompts/gloss.md`；脚本 `scripts/gloss.py`（make / check / merge）；数据 `work/gloss/G0001–G0062`（每块 1000 词）。
- 每个 Sonnet agent 写 2 块，提示词用 `bash work/tmp/glossprompt.sh G00xx G00yy` 生成。进度看 `gloss.py check`（显示还缺哪些块）。
- 全部完成后跑 `gloss.py merge`，生成 `work/merged/gloss.jsonl` 和 `gloss-skips.jsonl`。
- **已完成（2026-11-19）**：62 块全部通过校验并合并。
  - `work/merged/gloss.jsonl` 共 **45,667 条**简释，其中 93 条带 nokid。
  - `gloss-skips.jsonl` 共 15,409 个：unknown 14,554、not-english 499、not-lemma 211、junk 95、proper 50。
  - 额度：5 小时窗口 7%→43%（约 0.6%/块）；周额度 64%→69%；约 1 小时。
  - 各块跳过率差别很大（3%–80%），主要取决于字母段：化学、矿物、医学词集中的段落 unknown 多，non-/neo- 派生词多的段落覆盖率高。
- **Opus 重试 unknown（2026-11-19，用户同意）**：用 `gloss.py make-unknown` 把 14,554 个 unknown 切成 U0001–U0015，交给 Opus 再判断一遍（提示模板在 `work/tmp/opusgloss.txt`，每个 agent 2 块）。
  - 试点 U0001：写出 426 条，574 个仍 unknown，抽查准确，每块约 2% 的 5 小时额度。
  - 全部完成后重跑 `gloss.py merge`：U 层写出的简释会覆盖 G 层的 unknown，source 记为 gloss-v1-opus。**merge 之后不要再跑 make-unknown**，否则 U 块会重新切分。
  - **已完成**：15 块共新增 **2,692 条**（试点 U0001 是 43%，其余各块 9–41%，后面字母段更冷僻）。合并后 gloss.jsonl 共 **48,359 条**，gloss-skips 剩 12,717 个。额度：5 小时 3%→16%，周额度 69%→71%。
  - G0026–27 曾被怀疑偷懒而重写，结果相近，原稿保留为 *.lazy.txt。

### 1+2+3 扩展（2026-11-19 用户决定，已完成）

1. **变形索引**（`scripts/inflect.py`，零额度）→ `work/merged/inflections.jsonl`，每行 `{form, lemmas:[{lemma,types,src}], headword}`。
   - 来源：主词典 inflections（main）、ECDICT exchange（ecdict，要求 zipf ≥ 1.5 去噪）、not-lemma skip 的手工表 + 去后缀/拉丁复数规则（manual / rule）。
   - 43,970 个形式，827 个本身也是词头（left、saw）。not-lemma skip 389 个覆盖 304；剩下 85 个是原词不在词典里（strew、chid）。
2. **专名层**（`scripts/proper.py` + `prompts/proper.md`，Sonnet）→ `proper.jsonl`（`{word, display, names:[{type,zh,note}], also_common}`）、`proper-common.jsonl`（普通漏词，gloss 格式）、`proper-skips.jsonl`。
   - 候选：wordfreq zipf ≥ 3、主词典/简释层/变形索引都没有的 5,704 词，切 P0001–P0012（每块 500）。
   - 结果：专名 4,272、普通词 366、skip 1,066（unknown 554、junk 296、fragment 135〔angeles、kong 这类多词名碎片〕、not-english 71、numeral 10）。抽查译名准确。
   - 额度约 5 小时窗口 5%。
3. **短语层**（`scripts/phrase.py` + `prompts/phrase-writer.md` / `phrase-supp.md` / `phrase-reviewer.md`）→ `phrases.jsonl`（`{phrase, type, senses:[{pos,zh,en_short,tags}], level, flags}`）、`phrase-deletes.jsonl`。
   - 输入：主词典 zipf 前 6,000 个小写词头，切 Q0001–Q0060（每块 100 词）。Opus 写手（effort=low，每人 3 块）写 phrv / idiom / phrase / compound 四类，compound 补上了主词典没有的分写复合词（ice cream、high school）。
   - 前几块写得偏保守，写手规则加了「逐词四问」；之后对产出偏少的 23 块做补写（`Q*.supp.txt`，只补缺的）。写手 4,687 + 补写 814 → 去重 4,955。
   - 审核：切 R0001–R0013（每块 400），Opus 只写改正行或 `delete:<free|rare|proper|wrong|variant>`。改 82、删 175（free 130）。**没有仲裁**，审核结果直接生效。
   - 最终 **4,780 条**：phrase 1,311、compound 1,242、idiom 1,237、phrv 990；级别以 B2–C1 为主。
   - 额度：整个 1+2+3 约 5 小时窗口 17%→35%，周额度 71%→73%。
   - 已知：后段（Q0046 起，词频 4,500 名以后）每块只有 20–40 条，属正常下降；短语没有频率数据，发布时要另想排序（按 level 或按所属词头的 zipf）。

### 扩词第二轮（2026-11-19，用户：「再增加一下词吧」）

- **专名层扩到 zipf ≥ 2**：`proper.py make --min 2.0` 追加 P0013–P0076（31,937 词；make 会跳过已切过的词，编号接着排）。
  - 产出随频率下降：P0013 约 70%，P0030 约 34%，P0047 以后约 20–25%。
  - 合并后 proper.jsonl **12,954 条**，proper-common **2,568 条**，skip 22,119（unknown 18,494、junk 1,246、not-english 900、fragment 381）。
  - 已知：proper.py 的 Display 校验不认重音和撇号，所以 L'Oréal 写成了 LOreal、Dennys 等；中文栏不许字母，三K党成员 被改写。发布前可放宽校验后让模型修这些行。
- **短语层扩到前 10,000 词头**：`phrase.py make --top 10000`（前 60 块输入不变）追加 Q0061–Q0100，后段每块 10–40 条。
  - `phrase.py dedup --append` 只把新短语切成 R0014–R0016（850 条），旧审核结果不动。审核改 15、删 22。
  - 合并后 phrases.jsonl **5,608 条**。
- 额度：5 小时窗口 35%→59%，周额度 73%→77%。

### 短语层大扩充（2026-11-20，用户：「按三个方向补，尽量省 token」）——✅ 已完成

脚本 `scripts/phrase_more.py`（make-verbs / make-idioms / make-cands / triage-check / make-strict / make-compounds），产出仍用 `phrase.py check / dedup --append / merge`。
1. **短语动词** V0001–V0026（主词典前 1 万词里的 2,502 个动词，每块附 `.have.txt` 已有短语）→ Opus low，prompt `phrase-verbs.md`。✅ 已完成，约 1,300 条。
2. **习语** I0001–I0011（`prompts/idiom-themes.txt` 42 个主题，已有习语在 `idioms-have.txt`）→ Opus low，prompt `phrase-idioms.md`。✅ 已完成，约 1,600 条。
   - V + I 去重后 2,465 条，已切成审核块 **R0017–R0023（未审核）**。
3. **复合词**：ECDICT 2–3 词、由前 2 万常用词组成的 146,536 条 → K0001–K0049 Sonnet 初筛（`phrase-triage.md`）保留 15,189（偏松，部分块 15–22%）→ L0001–L0006 Sonnet 严筛（`phrase-triage2.md`）保留 9,960（仍偏松，约 70%）→ 已切成 **C0001–C0034（每块 300，未写）**。
   - 写手 prompt `phrase-compound.md` 已改严：只写 OALD 级别的条目，拿不准就不写，预计删掉约三分之一。
- 复合词写手 C0001–C0034（Sonnet，每人 4–6 块）写出约 6,200 条；去重（与已有短语重复的不再送审）后 5,124 条 → R0024–R0036。
- 审核 R0017–R0036（Opus，每人 2–3 块）：改 205、删 865。复合词块删得最多（rare 为主，另有 play list / post card 这类本应连写的 delete:wrong）。
- **合并后 phrases.jsonl 12,332 条**（上轮 5,608），phrase-deletes 1,062 条。级别以 C1（5,554）、B2（3,413）为主。
- 额度：第一段 5 小时窗口 59%→80%；窗口重置后第二段 11%→23%；周额度共 77%→86%。

### 短语层第四轮：类别横扫 + 查漏（2026-11-20，用户：「做 1 和 2」）

- **类别横扫** F0001–F0008（`prompts/phrase-themes.txt` 24 类：口语、介词短语、学术连接语、成对词、明喻、谚语、商务、时间、数量、科技等；prompt `phrase-themes.md`，Opus low）写出约 1,560 条，但大多数已经有了。
- **查漏**：Opus 凭记忆列常用短语动词和习语清单（`work/phrase/audit/`，prompt `phrase-audit.md`）共 3,340 条 → `phrase_more.py audit-diff` 对比现有，缺 749 条（覆盖率约 78%）→ G0001–G0003 Sonnet 写出 635 条。
- 去重后新增 1,055 条 → R0037–R0039 Opus 审核（改 14、删 38）。
- 合并后 phrases.jsonl **13,349 条**。查漏说明主流常用短语已基本收全，继续扩的边际收益很小。
- 额度：5 小时窗口 23%→约 36%，周额度 86%→87%。

### 搭配层（2026-11-20，用户：「那就上搭配层吧」）

- 脚本 `scripts/colloc.py`（make / check / merge），规则 `prompts/colloc.md`，数据 `work/colloc/K0001–K0050`（主词典 zipf 前 5,000 个有 n./v./adj./adv. 义项的词头，每块 100）。
- 格式：`collocation | pattern | 中文 | headword`，pattern 为 v+n / adj+n / n+n / adv+adj / v+adv / v+prep；不写英文释义（省 token）。
- 试点 K0006 后规则加了「中国学习者会不会选错词」的测试，排除普通组合、介词短语、专名、已在短语层的复合词（试点稿存为 K0006.pilot.txt）。
- Sonnet 每人 3–4 块。K0007–K0009 第一稿太粗（430–590 条）存为 *.rough.txt 后重写；K0001（最高频词）只写了 71 条，补写到 191 条。
- 合并：写手共 8,751 条 → 去掉与短语层重复的 1,516 条 → **collocations.jsonl 6,809 条**（adj+n 2,277、v+n 1,565、n+n 1,333、v+prep 871、adv+adj 468、v+adv 295）。同一搭配挂在多个词头下时 headword 为列表。
- **审核**（同日，用户：「额度够的话现在审」）：`colloc.py review-make` 切 J0001–J0018（每块 400），Opus 按 `prompts/colloc-reviewer.md` 审，`review-apply` 应用。
  - 改 224，删 1,793（free 1,021、phrase 714、rare 32、wrong 26）→ **collocations.jsonl 5,016 条**，全部 review_status=reviewer-ok/fixed，confidence=medium。删除记录在 `colloc-deletes.jsonl`；审核前版本备份为 `work/colloc/collocations.prereview.jsonl`。
  - **注意：不要再跑 `colloc.py merge`**，它会用写手稿覆盖审核后的结果；要重来就先 merge 再 review-apply。
  - 被判为 `phrase` 的 714 条（短语性质的搭配）目前只在 deletes 里，以后可挑出不在短语层的交给短语写手。
- 额度：写手 周额度 87%→89%；审核 89%→90%，5 小时窗口 43%→56%。

### 发布脚本与质量抽检（2026-11-20，用户目标：「世界上最好、小作坊都能直接用」）

- **发布**：`scripts/release.py [--version 0.9.0]`，16 秒，纯脚本，可重复跑。
  - 主词典按 zipf 生成最终 `rank`；各层统一 `id / layer / confidence / reviewed`，中文释义统一成字符串。
  - 输出 `release/<版本>/`（已在 .gitignore）：`jsonl/`、`csv/`、`open-learner-dict.sqlite`（含 `lookup` 表：任意写法 → 层和 id）、`wordlists/`、`MANIFEST.json`。
  - v0.9.0 条数：core 86,851（105,257 义项）、gloss 50,927（含专名层补的普通漏词，去掉与主词典重复的）、proper 12,954、phrases 13,346、collocations 5,016、inflections 43,937。
  - `scripts/make_schema.py`：生成 `schema/*.schema.json` 并逐行校验发布包（不依赖第三方库），全部通过。
  - 文档：`docs/DATA.md`（文件、字段、查词 SQL、已知局限）、`README.md`、`NOTICE.md`。
- **抽检**：`scripts/audit.py sample / check / report`，规则 `prompts/audit.md`。主词典按 rank 分 5 段各 100 条，其余四层各 100 条，3 个 Fable agent 各判 300 条。
  - 结果：900 条里 major 2（都在简释层）、minor 57。主词典 major 0、minor 21（4.2%）。
  - **抽检偏松**：按更严口径主词典约 1% 有释义用词错误（turnip→萝卜、qualitative→质量的 等）。解读和系统性问题清单写在 `reports/quality-0.9.0.notes.md`（report 时自动附在统计表后）。
  - 系统性问题（v1.0 前要修）：① word_family 混入不同源的词（约 2%）；② 非标准词头（living-room、ngo、kw，约 1%）；③ 搭配 pattern 需拆出 adj+prep / n+prep / n+v；④ 短语连字符写法（runner up）。
- 额度：周额度 90%→约 91%，Fable 36%→约 38%。

### 四类系统性问题的定向修正 → v0.9.1（2026-11-20）

- `scripts/fixes.py make / check / apply`，规则 `prompts/fixes.md`，数据 `work/fixes/`（H 词头、Y 短语写法、C 搭配分类、F 词族）。8 个 Sonnet，只输出要改的行。
- 结果：`work/merged/core-fixes.jsonl` 1,233 条（改大小写 72、加 standard_form 792、词族 369）；搭配 pattern 改 421；短语改写 40、移出 166（存 `phrase-solid.jsonl`，其中主词典没有的 56 个由 release.py 转进简释层）、去重 29，短语剩 13,153。
- 修正前的 phrases / collocations 备份在 `work/fixes/*.prefix.jsonl`。**apply 只能跑一次**（它改写 merged 里的 phrases 和 collocations）。
- `data/errata.jsonl`：勘误表（sense_id → 新 zh / en_short），release.py 每次自动应用；现有 6 条来自抽检。
- 发布版改为 **v0.9.1**（`release/0.9.1/`；0.9.0 目录已删，抽检报告仍叫 quality-0.9.0，说明里写了修正情况）。core 增加可选字段 `standard_form`，CSV 和 SQLite 同步加列。
- 没做的：3 万名以后的词族；H 的判断有些偏严（teabag、passionfruit 两种写法都通行），但只是加了 standard_form，不影响查词。
- 额度：这一轮周额度 91%→94%，5 小时窗口 56%→81%。**周额度已接近 95% 上限，重置前不要再派 agent。**

### 繁体中文（台湾用词）（2026-11-21，用户同意安装 opencc-python-reimplemented）

- `scripts/hant.py make / check / apply`，规则 `prompts/hant.md`，数据 `work/hant/`（T01–T27 释义 65,137 行；N01–N06 专名 13,126 行）。
- 做法：OpenCC `s2twp` 转出初稿 → 模型只输出要改的行（T 用 Sonnet 每人 3 块，N 用 Opus low 每人 2 块）→ `apply` 生成 `data/hant-overrides.jsonl`（78,188 条 = 校对范围内全部 key 的最终繁体；模型改了 3,987 条）。
- **教训：s2twp 的词组模式偏电脑术语，会误伤普通文本**（窗口/视窗→都成視窗，类型→型別，发布→釋出，通过→透過，安全局→安全域性）。所以：
  - 发布时没进校对范围的（主词典 3 万名以后、简释层）用 `s2tw`（只转字形）+ `data/hant-terms.tsv`（约 75 个无歧义台湾用词）；
  - 校对范围内模型没改、但仍含已知误伤词或重复项的 75 条，apply 时不写覆盖，退回安全转换。
- 原文带拉丁/希腊字母的释义（CT、PDF、γ）不接受模型改写（校验不许输出字母，模型只能硬改）。
- release.py：所有层输出 `zh_hant`（专名另有 `note_hant`），CSV / SQLite / Schema 同步；`docs/DATA.md` §5.1 说明来源。
- 没做的：香港用词；3 万名以后专业术语的台湾说法；繁体没有抽检过。
- 额度：周额度 2%→5%，5 小时窗口 12%→约 38%（Sonnet 每个 agent 约 30 万 token，比预想的贵）。

### compact 后从这里继续（2026-11-26 现状与下一步）

- **当前基线**：`v0.10.0` 已正式公开推送至 `https://github.com/greypapl/open-learner-dict` 并发布 GitHub Release（含 SQLite / JSONL / CSV / wordlists 四个压缩包与 `SHA256SUMS.txt`），`make_schema.py` 全过。
  - 各层条数：`core` 86,851（105,257 义项；前 1 万 + 全部 A1–C1 共 29,034 条例句、28,912 个义项同反义词）、`gloss` 50,969（一轮 Opus 审，confidence=low）、`proper` **12,928**（两轮审完，confidence=medium）、`phrases` 13,153、`collocations` 5,016、`inflections` 43,919；全层 `zh_hant` 已校对；SQLite 体积 73.2 MB（压缩包 27.55 MB）。
- **专名层二轮已收口（2026-11-26）**：见下方「专名层第二轮审核完成」；核心口径已固化（`Chewbacca`/`Chewie` = 楚巴卡/楚伊；知名品牌如 YouTube/Instagram/JCB 允许保留拉丁原名；`p_oreal` 已删、`p_artagnan` 暂保留）。
- **下一步优先级**：
  1. **接入「单词接龙」小程序**（工作区 `C:\Users\greypapl\Desktop\新同步文件夹\单词接龙源码\单词接龙`；完整 SQLite 73.2 MB，移动端需另做精简包）。
  2. **v1.0.0 候选增强**：按词性分音标（record/present 等，属 Schema 变更）、短语层补例句（1.3 万条）、导出 MDX / Anki 格式、简释层换强模型二审。
- **环境备忘**：若从「单词接龙」工作区启动会话，本仓库（`C:\Users\greypapl\project\整理单词`）在工作区外，执行 Python 脚本与 `git -C` 需用 `BypassSandbox: true`；子 agent 审核完毕后由主会话统一落盘并跑 `check`。

### 专名层第二轮审核完成（2026-11-26）→ release 0.10.0（重发）

- 用户要求在 v1 之后换更严格模型再审一轮。`scripts/proper_review.py --round 2`（目录 `work/proper-review2`，输出 `work/merged/proper-review2.jsonl`），prompt `prompts/proper-review2.md`（v1 prompt + 「第一轮太保守，你是更严格的第二轮」）。
  输入从当前发布包切（已含 v1 和人工补改），key 编号与 v1 兼容；`release.py` 按 `proper-review*.jsonl` 顺序读，后一轮覆盖前一轮。
- **已完成（P01–P06 由 Fable 审，P07–P09 由 Gemini 4 Neon 审）**：
  - 全量 9 块通过 `check --round 2`（0 格式错误）：合计改/增名字 **539**（大陆译名变 165）、去名字 0、改写法 4（含 `Cape Town`、`Ant-Man`）、删词条 3（`p_oreal` 与 `p_loreal` 重复残片、`p_pipa`、`p_bodhisattvas`）。
  - 试点对比：P04 Opus 第一轮改译名 14 个，Fable 第二轮又改 33 个（巴麦尊、皮尔士、米洛、蒙纳士大学、Brahman→梵）；P07–P09 亦查出多处张冠李戴（Laois 劳斯郡→莱伊什郡、Pentonville 本顿维尔→彭顿维尔）与繁简误转。
  - 人工核对决断：`Chewbacca`/`Chewie` 二轮已统一为「楚巴卡 / 楚伊」（台「秋巴卡 / 秋仔」）；允许品牌词中文/台湾栏保留拉丁原名（YouTube、Instagram、JCB）。
  - `release/0.10.0` 已重发，Schema 校验全过：proper 12,931 → **12,928**，`confidence` 升为 `medium`，`meta.review = "proper-review-v2"`。
- 遗留：`p_artagnan`（Artagnan）是切词残片（应为 d'Artagnan，因词库无 `p_dartagnan` 暂保留；`p_oreal` 已删）。

### 专名层审核 v1 完成（2026-11-22）→ release 0.10.0（重发）

- 新脚本 `scripts/proper_review.py`（make / check / apply → `work/merged/proper-review.jsonl`），prompt `prompts/proper-review.md`。
  每个名字一行 `<p_id>#<i> | Display | type | 中文名 | 说明 | 台湾译名`，9 块 P01–P09（每块 1,500 行），Opus 默认 effort。
  审核员改大陆名时**同时给台湾名**，release 里审过的名字直接用审核给的台湾名（覆盖 `data/hant-overrides.jsonl`），所以省掉了原计划的第 6 步（单独补校繁体）。
- 结果：改名字 363（译名变约 130，新增名字 20+），改写法 39，删词条 23 → proper 12,954 → 12,931。
  - 模型提了 65 个删复数，人工只留了品牌/缩写/姓氏的复数（iPhones、KPIs、Johnsons）；**民族、教派、组织、家族的复数**（Houthis、Habsburgs、Gurkhas、Huguenots）恢复保留——它们通常就用复数，专名又不在变形索引里，删了查不到。
  - display 校验放宽到允许改空格和 `!`（Super Bowl、Yu-Gi-Oh! 是人工补的）。
- **召回仍低**：抽检 26 条只主动改到 11 条（试点块 4/6），Hercules 还改错（留着希腊名）。其余 15 条人工按抽检补改。所以 `confidence` 仍 low、`reviewed=true`。
  prompt 已经写得比简释层宽松，召回还是 42%——**单轮 Opus 审核对这类「有更通行译名」的问题天然偏保守**；要再提高大概得换 Fable 再审一轮（抽检就是 Fable 做的、查出了这些）。
- 额度：9 块各约 13–15 万 token，5 小时窗口 45%→55%（9 块合计约 10%），周额度 30%→31%。

### compact 后从这里接着做：专名层审核（已完成，见上一节；以下保留作记录）

**现状（2026-11-21 收工时）**：release 0.10.0，全部已提交（最新 `0f3e943`，工作区干净）。各层：
主词典 86,851（审过；例句 29,034 条 + 同反义词 28,912 个义项，范围都是「前 1 万名 + 全部 A1–C1」）、简释 50,969（审过一轮，召回低，confidence 仍 low）、
**专名 12,954 个词条 / 13,126 个名字（唯一完全没审过的一层）**、短语 13,153、搭配 5,016、变形 43,919。繁体：释义/短语/搭配/专名/例句都校对过。
抽检报告 `reports/quality-0.10.0.md`（audit-v2，Fable，2,100 条）：专名层 major 1%、minor 8%，minor 大多是「有更通行的大陆译名」（班克斯→班克西、廷德尔→丁达尔、塞尔福里奇、迈赫迈特、Hercules 罗马名应作海格力斯），
另有个别 type 标错（Byrds 乐队标成 work）、note 过窄（Fawcett 只写「美国女演员姓氏」）、复数不该立条（Macs）。

**做法（照 `scripts/gloss_review.py` 的套路，已验证可用）**：
1. 新脚本 `scripts/proper_review.py`：`make` 从 `release/0.10.0/jsonl/proper.jsonl` 每个名字一行：`<p_id>#<序号> | Display | type | 中文名 | 说明`，每块约 1,500 行（约 9 块）；
   `check`；`apply` → `work/merged/proper-review.jsonl`。
2. 审核输出只写要改的行：`<p_id>#<序号> | type | 中文名 | 说明`；删词条：`<p_id> | delete | 原因`（只删不是专名的、拼写错误、无意义的复数形式）。
3. prompt `prompts/proper-review.md`：标准是大陆通行译名（新华社译名、百科常用名）；type 只能是 person place brand org abbr work people religion event other；
   **不确定就别改**这句要写得比简释层宽松（简释层就是因为这句太保守，独立抽检的错只改到一半）：改成「有把握的通行译名就改；冷门人名若无通行译名，保留音译即可」。prompt 里的示例不要用抽检查出的那几条（会让召回测试失真），抽检那几条留作试点后的召回检查。
4. 模型：Opus（默认 effort）。先试点 1 块，看改动率和质量，再派其余块。
5. `release.py` 的专名层部分读 `work/merged/proper-review.jsonl`：改 type/zh/note、删词条、`reviewed=true`、confidence 视召回情况定（Schema 里 proper 的 confidence 目前只允许 low，要改 `make_schema.py`）。
6. **注意繁体覆盖**：`data/hant-overrides.jsonl` 里有 13,126 条 `p_<slug>#<i>` 的台湾译名（模型校对过）。如果审核改了大陆译名，对应的台湾译名可能也要变（尤其是原来译错人的情况）。
   做法：apply 后列出「大陆名改了」的 key，交给 Sonnet 按 `prompts/hant.md` 的 N 规则重新给台湾名，写进覆盖表（可以在 hant.py 里加一个 N2 前缀或直接生成小块）。
7. 发布 → Schema → DATA.md（「proper 层未经审核」那句）/ README（专名「未审核」）/ 本节 → 提交。

**额度经验（本轮实测）**：Opus 审 2,000 行约 13–20 万 token ≈ 5 小时窗口 0.7%；Opus low 写 400 行同反义词 ≈ 0.3%；Sonnet 校繁体 2,500 句 ≈ 15 万 token。闸门照旧：5 小时 ≥ 90% 或周额度 ≥ 95% 就停派。

**专名层之后的建议顺序**（2026-11-21 跟用户讨论过）：
1. **接入单词接龙 app**（第一个真实用户；可顺便做「接龙专用精简包」——SQLite 现在 67 MB，手机端偏大）。
2. **正式发布**：GitHub 仓库 + Releases 放 zip；发布前核对上游许可（ECDICT MIT、wordfreq 数据 CC BY-SA、CMUdict BSD、OpenCC Apache）和 NOTICE。推送是对外操作，要先问用户、用用户自己的账号。
3. 其余候选：按词性分开给音标（record/present 名动重音不同，是格式变更）、短语层例句（1.3 万个，约 40% 窗口）、简释层换 Fable 再审、MDX/Anki 导出。

### 例句层 v1 完成（2026-11-21）→ release 0.10.0

- 前 5,000 词 11,658 个义项全部有 1 句例句（`scripts/examples.py`，prompts `example-writer.md` / `example-reviewer.md`）。
- 写手 Opus low：39 块 × 300，13 个 agent，每个约 13 万 token；审核 Opus：6 块 × 2,000，每个约 20 万 token，共改 97 条（0.8%）。整轮约占 5 小时窗口 15–20%，周额度约 1–2%，比预估省很多。
- 产物：`work/merged/examples.jsonl`；release 0.10.0 的 `senses[].examples`、`csv/examples.csv`、SQLite `examples` 表；Schema 全部通过。例句繁体只做安全转换。
- **排名修正（同日）**：wordfreq 把 `so-so` 拆成 so + so 算频率，338 个带连字符/空格的词头排名虚高（so-so 原排第 59）。ECDICT 对这些词没有 COCA/BNC 词频，所以 release.py 改用「同 CEFR 级别单词 zipf 的中位数，且不高于原值」，新字段 `zipf_source = level-estimate`（core、gloss、CSV、SQLite、Schema 都已同步）。修后 so-so 第 3807、well-being 第 7309，前 5,000 里这类词从 288 个降到 47 个。
- 修正后新进前 5,000 的词补了 471 个义项（E0040–E0041，审核 V0007 改 7 条）。现在共 12,129 条例句，覆盖 5,241 个词，前 5,000 名零缺口；审核共改 104 条。
- **扩到前 1 万（完成）**：E0042–E0070（8,563 条）+ 审核 V0008–V0012（改 103 条）。现在共 **20,692 条例句**，覆盖 10,143 个词，前 1 万名零缺口；审核共改 207 条（1.0%）。release 0.10.0 已重新生成，Schema 通过。这一轮写手 10 个 agent 约 125 万 token，但 5 小时窗口从 60% 涨到 92%，比前一轮贵（原因不明）。
- **A1–C1 全补（完成）**：`make --top 10000 --max-level C1` 新增 8,307 个义项（E0071–E0098，审核 V0013–V0017 改 65 条）。现在共 **28,999 条例句**，覆盖 16,023 个词；前 1 万名和全部 A1–C1 零缺口，审核共改 272 条（0.9%）。这一轮写 + 审约占 5 小时窗口 30%。
- **人名同形词排名修正（完成）**：`scripts/zipf_overrides.py` → `data/zipf-overrides.tsv`（97 条，release.py 读取）。① coca 51 条：C1/C2、zipf ≥ 3、ECDICT 的 COCA 词频（frq，按普通词用法统计）推出的 zipf 比 wordfreq 低 1.5 以上 → 用 COCA 推算值（john 342 → 14710、cooper → 27511，也抓到 trying/considered 这类形容词词条，频率其实来自动词形式）；② manual 46 条：COCA 没数据的人名/姓氏同形词（smith、lee、turner、warren…），用同级别中位数。脚本读 `work/merged/B*.jsonl` 原值，可以重复运行。前 5,000 里剩下的 C2 词基本是真实高频的古语/俚语（thou、ye）和真词（jurisdiction、vector）。修正后新进前 1 万的 35 个义项补了例句（E0099，我自己审，无改动）。COCA 没数据、又不是人名的高频 C1/C2 词（mindset、crypto、criterion）没动，频率是真的。
- `examples.py make` 和 `review-make` 都已改成**增量**：已切过块的 sense_id 不再切，新块接着编号。扩到前 1 万词直接 `make --top 10000 --version 0.10.0` → `check` → `review-make` → 审核 → `apply` → 发布。

### （已完成）例句的原计划

**目标**：给主词典前 1 万常用词的每个义项写 1 句英文例句 + 简体译文 + 繁体译文，填进 `senses[].examples`（现在全是空数组）。

**规模**：前 1 万词共 20,450 个义项（前 5,000 词 11,658；前 2 万 34,757；前 3 万 46,332）。短语层另有 13,789 个义项，这一轮不做。

**token 估算**（参照短语层和繁体校对的实际消耗）：
- 写手：每条例句约 60 个输出 token（英文 12 词 + 中文）；每块 300 个义项，每个 agent 3 块，约 12–15 万 token。约 23 个 agent → **约 300 万 token**。
- 审核：每块 2,000 条，每个 agent 2 块，约 25 万 token。约 6 个 agent → **约 150 万 token**。
- 合计 **约 450–500 万 token**。折算：Opus 写 + Opus 审，约占一个 5 小时窗口的 70–90%，周额度约 8–10%；写手换 Sonnet 可降到约一半，但例句自然度会差一些。
- 省钱办法：先只做前 5,000 词（约 250 万 token）；繁体译文不让模型写，用 `hant.py` 的办法转（安全转换 + 用词表），以后再校对。

**建议的做法**（都还没写，照 phrase / colloc 的套路）：
1. `scripts/examples.py make`：从 `release/0.9.1/jsonl/core.jsonl` 取 rank ≤ 10000 → `work/examples/E0001.in.txt`，每行 `sense_id | word | pos | zh | en_short`。
2. `prompts/example-writer.md`：每个义项 1 句；8–14 个词；用词不超过该词级别太多（A1–B1 的词用简单句）；必须体现这个义项而不是别的义项；例句里原词可以用变化形式；不出现真实人名、品牌、敏感内容；输出 `sense_id | 英文例句 | 中文译文`。
3. `check`：sense_id 都在、句子含原词或其变形（用 inflections.jsonl 判断）、长度、中文无字母。
4. 试点 1 块（Opus low），抽查后再批量；写手 5 个并行，每人 3 块。
5. `prompts/example-reviewer.md` + Opus 审核：只输出要改的行（译文不准、例句体现的不是该义项、不自然）。
6. `apply` → `work/merged/examples.jsonl`（{sense_id, en, zh}）；release.py 读它填 `examples: [{en, zh, zh_hant}]`，Schema、DATA.md、CSV（新 `examples.csv`）、SQLite（新 `examples` 表）同步。
7. 做完重新发布（版本号升到 0.10.0，因为新增了内容），再抽检一次。

**注意事项（踩过的坑）**：
- Bash heredoc 里的反斜杠转义（反斜杠加 n、b、d、竖线）会被吃掉或报错：改脚本一律用 Write 工具写一个补丁脚本到 scratchpad 再运行，或直接 Write 整个文件。
- 让模型「只输出要改的行」很省 token，但要在 check 里校验 key 存在；有的 agent 会把整行抄回来，check 要能兼容。
- 校验规则别太死（比如不许字母），否则模型会为了过校验而硬改内容。
- `colloc.py merge`、`fixes.py apply` 都是一次性的，不要重跑（见各自小节）。
- 额度闸门照旧：5 小时窗口 ≥ 90% 或周额度 ≥ 95% 就停。现在周额度约 5%（2026-11-27 23:00 重置）。
- 全部改动自 2026-11-20 起**没有提交 git**（约 50 多个文件，含 scripts/、prompts/、docs/、schema/、data/、reports/ 和 work/ 下的新数据），用户还没说要提交。

**例句之后的候选**：更严口径、换模型重新抽检（每层 300 条，含繁体）→ 3 万名以后的词族检查 → 同反义词 → 简释层和专名层审核 → MDX / Anki 导出。

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
