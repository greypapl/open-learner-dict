# 数据说明 · open-learner-dict v0.9

本文说明发布包里每个文件、每个字段的含义。发布包由 `scripts/release.py` 生成，位于 `release/<版本>/`。

## 1. 先看这里：该用哪个文件

| 你要做什么 | 用哪个文件 |
|---|---|
| 在应用里查词（推荐） | `open-learner-dict.sqlite`，先查 `lookup` 表 |
| 用表格软件或脚本看数据 | `csv/*.csv`（UTF-8 带 BOM，Excel 可直接打开） |
| 要完整字段、自己处理 | `jsonl/*.jsonl`（每行一个 JSON 对象） |
| 只要词表 | `wordlists/*.txt`（每行一个词） |

所有文件内容相同，只是格式不同。`MANIFEST.json` 里有版本号、各层条数和每个文件的 sha256。

## 2. 六个层

词库分层存放，**可信度不同，不要混用而不加区分**。每条数据都有 `layer`、`confidence`、`reviewed` 三个字段。

| 层 | 文件 | 内容 | 怎么来的 | confidence |
|---|---|---|---|---|
| core | core | 主词典：释义、音标、音节、词族、级别 | Opus 写 → Opus 审 → 有分歧由 Fable 仲裁 | high / low |
| gloss | gloss | 冷僻词：只有一行中文简释 | Sonnet / Opus 写 → Opus 审一轮（召回偏低） | low |
| proper | proper | 专名：地名、人名、品牌、机构缩写的中文名 | Sonnet 写 → Opus 审一轮（召回偏低） | low |
| phrase | phrases | 短语动词、习语、固定短语、分写复合词 | Opus / Sonnet 写 → Opus 审 | medium / low |
| collocation | collocations | 强搭配（make a decision、heavy rain） | Sonnet 写 → Opus 审 | medium |
| — | inflections | 变形索引：went → go | 脚本生成 | — |

- `confidence=high`：常用词，写手和审核一致。`low`：罕见词、专业词，或模型自己标了没把握。主词典里 zipf 较低的词统一为 low。
- 全程**没有人工校对**。错误率估计见 `reports/quality-<版本>.md`。
- 给儿童或游戏用：core 用 `kid_safe` 和 `game_ok` 筛；其他层用 `kid_safe`。

## 3. 查词流程（SQLite）

```sql
-- 任何写法（单词、变化形式、短语、搭配、专名）先查 lookup，key 一律小写
SELECT layer, id FROM lookup WHERE key = lower(:q);
-- layer = core / gloss      → entries + senses（id 是 entries.id）
-- layer = inflection         → id 是原词的 entries.id（went → go 的 id）
-- layer = proper             → proper + proper_names
-- layer = phrase             → phrases + phrase_senses
-- layer = collocation        → collocations

SELECT e.word, e.ipa_us, e.level, s.pos, s.zh, s.en_short
FROM entries e JOIN senses s ON s.entry_id = e.id
WHERE e.id = :id ORDER BY s.idx;

-- 义项的同义词 / 反义词
SELECT type, related FROM sense_relations WHERE sense_id = :sense_id ORDER BY type, idx;
-- 反查：哪些义项把 quick 列为同义词
SELECT sense_id FROM sense_relations WHERE related = 'quick' AND type = 'synonym';

-- 义项的例句（前 1 万名和 A1–C1 的词都有）
SELECT en, zh, zh_hant FROM examples WHERE sense_id = :sense_id ORDER BY idx;

-- 某个词的短语和搭配
SELECT phrase FROM phrases WHERE phrase LIKE 'give %';
SELECT c.collocation, c.zh FROM collocation_headwords h JOIN collocations c ON c.id = h.collocation_id WHERE h.headword = 'decision';
```

同一个 key 可能命中多层（`left` 既是 core 词条，也是 leave 的变形），应用应把它们都展示出来。

## 4. core：主词典字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 稳定 ID（`w` + 6 位数字），不会复用 |
| `word` | string | 词头，保留大小写（`Monday`、`USB`） |
| `standard_form` | string，可选 | 只有词头不是词典标准写法时才有，给出标准写法（`living-room` → `living room`）。约 800 条 |
| `rank` | int | 按 `zipf` 从高到低的名次，1 起 |
| `zipf` | number | wordfreq zipf 频率（约 0–8；≥ 4 属常用，< 2 很罕见）。0 表示 wordfreq 没有数据 |
| `zipf_source` | `wordfreq` \| `level-estimate` \| `coca-estimate` | 约 430 个词的 wordfreq 频率虚高，改用估计值（都不高于原值），排名只能作参考：① 带连字符或空格的词（约 340 个，如 `so-so`、`well-being`），wordfreq 会拆开算 → 同级别单词 zipf 的中位数（`level-estimate`）；② 和人名、品牌、动词变形同形的词（97 个，如 `john`、`cooper`、`trying` 的形容词义），wordfreq 统计的主要是人名或动词用法 → 按 ECDICT 的 COCA 词频推算（`coca-estimate`），COCA 没有数据的人名同形词用同级别中位数。修正表在 `data/zipf-overrides.tsv`，可以手改。简释层同样有这个字段，按 C2 中位数封顶 |
| `ipa_us` / `ipa_uk` | string | 宽式 IPA，不带斜杠。`ipa_us_source`：`cmu`（来自 CMUdict）或 `model`（模型写） |
| `syllables` | string | 拼写的音节切分，用 `·` 分隔 |
| `stress` | int[] \| null | 各音节重音（1 主、2 次、0 无），只有 CMUdict 有的词才有 |
| `senses[]` | array | 义项，**按现代常用度排序**，第一个最常用。每个词性最多 3 个，全词最多 6 个 |
| `senses[].sense_id` | string | 稳定义项 ID（`<id>.<序号>`） |
| `senses[].pos` | string | `n. v. adj. adv. prep. conj. pron. det. int. num. aux. abbr.`（不分及物不及物） |
| `senses[].zh` | string | 中文释义，1–4 个近义表达，用 `, ` 分隔 |
| `senses[].zh_hant` | string | 繁体中文（台湾用词）。来源见第 5.1 节 |
| `senses[].en_short` | string | 英文简释，≤ 12 词 |
| `senses[].register` | string[] | `formal informal slang dated literary uk us offensive-mild offensive-strong domain:<领域>` |
| `senses[].examples` | array | 例句 `[{en, zh, zh_hant}]`。**前 10,000 名的词、以及所有级别 A1–C1 的词（不论名次）全部有**，每个义项 1 句，共 16,044 个词、29,034 个义项。没有例句的只剩排名 1 万以后的 C2 词，为空数组。模型撰写、另一模型审核；`zh_hant` 只做安全转换（见 5.1） |
| `senses[].synonyms` / `antonyms` | string[] | 按义项的同义词（最多 4 个）和反义词（最多 2 个），**前 1 万名和全部 A1–C1 的词**都做了（28,912 个义项，其中 21,257 个有同义词、7,905 个有反义词；没有合适的就留空，如 giraffe、代词）。每一项都保证是本词典里的词条或短语，可以直接链接。模型撰写、另一模型审核（改 361 条）。CSV 在 `csv/relations.csv`，SQLite 在 `sense_relations` 表 |
| `inflections` | object | `plural past past_participle present_participle third_person comparative superlative` |
| `spelling_variants` | string[] | 同一个词的其他拼写（colour ↔ color） |
| `word_family` | string[] | 同词族的常用派生词，最多 6 个 |
| `affixes` | string[] | 可辨认的标准前后缀（`un-`、`-ness`） |
| `level` | string | CEFR A1–C2，**模型估计值**（`level_estimated` 恒为 true） |
| `exam_tags` | string[] | `zk` 中考、`gk` 高考、`cet4`、`cet6`、`ky` 考研。来自 ECDICT 的标签 |
| `offensive` | null \| `mild` \| `strong` | 冒犯程度 |
| `kid_safe` | bool | false = 不宜儿童（冒犯、色情、毒品、暴力） |
| `game_ok` | bool | false = 不适合拼词类游戏（缩写、专有名词、带连字符或撇号） |
| `confidence` | `high` \| `low` | 见第 2 节 |
| `review_status` | `agreed` \| `arbitrated` \| `disputed` | 写手审核一致 / 经仲裁 / 仍有分歧（只保留双方都同意的义项） |
| `meta` | object | 生产记录：模型、提示词版本、审核说明。应用可以忽略 |

## 5. 其他层字段

**gloss**：`id`、`word`、`zipf`、`senses[]`（`sense_id`、`pos`、`zh`、`register`）、`kid_safe`。没有音标、英文释义和级别。`id` 以 `x_` 开头的是整理专名层和短语层时顺带补的普通词（如 `double-check`）。

**proper**：`id`（`p_…`）、`word`（小写）、`display`（正常大小写写法）、`zipf`、`names[]`（`type`、`zh`、`note`）、`also_common`（true 表示它同时是个普通词）。
`type`：`place person brand org abbr work people religion event other`。中文名是大陆通行译名。已知问题：`display` 不含重音符和撇号（`LOreal`）。

**phrases**：`id`（`ph_…`）、`phrase`、`type`、`senses[]`（同 core，但没有 synonyms 等）、`level`、`kid_safe`。
`type`：`phrv` 短语动词、`idiom` 习语、`phrase` 固定短语、`compound` 分写复合词。短语里 `sb` / `sth` / `one's` 表示可替换的位置。短语没有词频数据，排序请用 `level`。

**collocations**：`id`（`c_…`）、`collocation`、`pattern`、`zh`、`headwords[]`（这条搭配挂在哪些词头下）。
`pattern`：`v+n adj+n n+n adv+adj v+adv adv+v v+prep adj+prep n+prep n+v`。

**inflections**：`form`、`lemmas[]`（`lemma`、`types[]`）、`is_headword`（这个形式本身是否也是词条，如 `left`、`saw`）。`types` 除了 core 的七种，还有 `present`（are → be）和 `archaic`（hath → have）。少数由规则推出的 `-s` 形式只记 `plural`，没有区分第三人称单数。

### 5.1 繁体中文（`zh_hant`）

所有层都有 `zh_hant`（专名层还有 `note_hant`），目标是台湾华语的写法和用词。

- **主词典前 3 万名、短语层、搭配层、专名层**：先自动转换，再由模型逐条按上下文校对台湾用词和译名（軟體、馬鈴薯、優格、歐巴馬、雪梨、賓士）。约 7.8 万条，其中模型改了约 4,000 条。
- **主词典 3 万名以后、简释层**：只做字形转换（OpenCC `s2tw`），加一张无歧义的台湾用词表（`data/hant-terms.tsv`，约 75 个词）。专业术语的台湾说法（如化学、医学名词）可能没有转对。
- 没有用 OpenCC 的词组转换模式（`s2twp`）做最终结果，因为它会把「窗口」「类型」这类普通词误转成电脑术语。
- **例句译文**：先做字形转换加用词表，再由模型逐句校对（2.9 万句，改了 1,604 句：分词误转如「英國曆史」→「歷史」、「遊了」→「游了」，以及台湾用词如 樂隊→樂團、計劃→計畫、酒店→飯店、發動機→引擎）。
- 香港用词没有单独处理。

## 6. 已知局限

- 没有人工校对；级别、冒犯程度都是模型判断。
- 发现的错误记在 `data/errata.jsonl`，每次发布时自动应用。
- 例句覆盖前 1 万名和全部 A1–C1 的词，排名 1 万以后的 C2 词没有；短语层还没有例句。同义词、反义词只覆盖前 1 万名和 A1–C1；发音音频还没有。
- gloss 层经过一轮 Opus 审核（`reviewed=true`，改 423 条、删 14 个拼写错误的词头），但审核偏保守：独立抽检查出的 12 条错误里它只主动改到 7 条（其余 5 条是人工按抽检结果补改的），所以估计仍有约 2–3% 的冷僻术语译名不准，`confidence` 仍为 low。proper 层也经过一轮 Opus 审核（`reviewed=true`，`meta.review = "proper-review-v1"`）：改了 363 个名字（其中约 130 个换成通行译名，如 班克斯→班克西、廷德尔→丁达尔、机器猫→哆啦A梦；其余是类型、过时说明、台湾译名），补了 20 多个漏掉的主要义项（Nobel → 诺贝尔奖、Rudd → 陆克文），修了 39 个写法（McDonald's、J.D.、Super Bowl），删了 23 个品牌/缩写/姓氏的复数词条（iPhones、KPIs；民族、教派、家族的复数如 Houthis、Habsburgs 保留）。但召回同样偏低：抽检查出的 26 条只主动改到 11 条（其余 15 条人工补改），估计仍有约 5% 的名字不是最通行的译法，`confidence` 仍为 low。两层都建议在界面上标明「仅供参考」。
- `zh` 是大陆用语和译名（软件、奥巴马）；台湾用语见 `zh_hant`。
- 主词典 86,851 条里约 7.2 万条是 C2 级的罕见词，学习类应用通常只需要 `rank` 靠前或 `level` ≤ C1 的部分。

## 7. 版本与许可

- 语义化版本：字段含义不变只加数据 → 小版本；改字段 → 大版本。`id` 和 `sense_id` 跨版本稳定。
- 数据：CC BY-SA 4.0（署名、相同方式共享）。代码：MIT。第三方来源见 `NOTICE.md`。
- 发现错误请提 Issue，写明 `id` 或 `sense_id`。
