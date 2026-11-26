# open-learner-dict

[![Release](https://img.shields.io/github/v/release/greypapl/open-learner-dict?include_prereleases&label=release)](https://github.com/greypapl/open-learner-dict/releases)
[![Entries](https://img.shields.io/badge/entries-169k%2B-blue)](#数据规模)
[![SQLite](https://img.shields.io/badge/SQLite%20zip-27.5%20MB-informational)](https://github.com/greypapl/open-learner-dict/releases)
[![Data License: CC BY-SA 4.0](https://img.shields.io/badge/Data-CC%20BY--SA%204.0-lightgrey.svg)](LICENSE-DATA)
[![Code License: MIT](https://img.shields.io/badge/Code-MIT-green.svg)](LICENSE)

**新一代开源结构化英汉双解词库（简繁双轨）** —— 零版权负担、全量从头撰写、多模型交叉审校，开箱即用。

**The modern, open-source, structured English–Chinese dictionary dataset** built from scratch — clean licensing, Simplified & Traditional Chinese (Mainland / Taiwan), bilingual examples, collocations, and an internal thesaurus graph out of the box.

> 当前版本 **v0.10.0**：包含主词典 **86,851 词**、冷僻词简释 **50,969 条**、专名 **12,928 条**、短语 **13,153 条**、强搭配 **5,016 条**、变形反查 **43,919 条**，并内置 **29,034 句双语例句** 与 **56,375 条同反义关系**。附完整 2,100 条独立分层抽检报告（[reports/quality-0.10.0.md](reports/quality-0.10.0.md)）。

---

## 为什么做 open-learner-dict？

现有开源英汉词库大多停留在「历史文本拼接」阶段：释义是一整段纯字符串、义项杂乱、来源版权模糊、缺乏例句与搭配、繁体靠机转频频误伤。**open-learner-dict** 从零按现代词典工程标准重建：

| 维度 | 传统开源词库（如 ECDICT） | **open-learner-dict** |
|---|---|---|
| **释义结构** | 单行纯文本拼接，难以程序解析 | **全结构化多义项**（`pos` + 中英双解 + 语域/领域标签） |
| **义项排序** | 历史堆叠，冷僻义常排前面 | **按现代常用度排序**，第 1 义项即最常用 |
| **版权与商用** | 多源聚合，释义来源复杂 | **零照抄商业词典**，释义全量原生撰写，**CC BY-SA 4.0 可商用** |
| **例句与同反义** | 无 | **29,034 句双语例句 + 5.6 万条站内闭环同反义词**（覆盖前 1 万 + 全部 A1–C1） |
| **短语、搭配、专名** | 混杂或缺失 | **独立分表**：13,153 短语 + 5,016 强搭配 + 12,928 两轮精校专名 |
| **简繁双轨** | 无，或 OpenCC 裸转（常见误伤） | **真·两岸用词双轨**：约 8 万条词义/专名 + 2.9 万句例句逐条校对台湾用词 |
| **质量透明度** | 无公开评估指标 | **写 → 审 → 仲裁三步流水线 + 置信度分层 + 2,100 条独立抽检报告** |
| **开箱接入** | 需自行清洗建索引 | **SQLite（内置统一 `lookup` 路由）+ JSONL + CSV + JSON Schema + 12 份词表** |

---

## 数据规模

所有数据按可信度严格分层存放，绝不把冷僻扩展词混入核心学习词：

| 层 | 规模 | 说明 | 可信度 / 抽检表现 |
|---|---|---|---|
| **主词典 `core`** | **86,851 词**（105,257 义项） | 中英双解、美英 IPA、音节、重音、词族、前后缀、CEFR（A1–C1 共 15,466 词）、中考/高考/四六级/考研标签、`kid_safe`、`game_ok` | `high` / `low`；抽检严重误导率 **~0.7%** |
| **例句 `examples`** | **29,034 句** | 覆盖**前 1 万常用词 + 全部 A1–C1 词**零缺口，每义项 1 句英文 + 简繁双轨译文 | 抽检严重错误 **0%** |
| **同反义 `relations`** | **28,912 义项** | 同义 **46,954 条** + 反义 **9,421 条**，每一项均保证链接到本词典已有词条或短语 | 写 + 独立审核 |
| **短语 `phrases`** | **13,153 条** | 短语动词 2,821 / 习语 4,050 / 分写复合词 4,225 / 固定短语 2,057 | `medium` / `low`；抽检 **~0.3%** |
| **搭配 `collocations`** | **5,016 条** | 前 5,000 实词强搭配（`make a decision`、`heavy rain` 等 10 种结构） | `medium`；抽检 **0%** |
| **专名 `proper`** | **12,928 条** | 地名、人名、品牌、机构缩写的中台通行译名 | `medium`（两轮全量审核） |
| **简释 `gloss`** | **50,969 条** | 冷僻/专业词一行中文简释（独立分层，按需启用） | `low`（一轮审核） |
| **变形索引 `inflections`** | **43,919 条** | 屈折变形反查原形（`went → go`、`children → child`） | 脚本精确生成 |

---

## 真实词条长什么样？

以下是 `release/0.10.0/jsonl/core.jsonl` 中的原样词条（`software`）：

```json
{
  "id": "w001592",
  "word": "software",
  "rank": 1361,
  "zipf": 4.77,
  "ipa_uk": "ˈsɒftweə",
  "ipa_us": "ˈsɔfˌtwɛr",
  "syllables": "soft·ware",
  "stress": [1, 2],
  "senses": [
    {
      "sense_id": "w001592.1",
      "pos": "n.",
      "zh": "软件, 软件程序",
      "zh_hant": "軟體, 軟體程式",
      "en_short": "programs used by a computer",
      "register": ["domain:计算机"],
      "synonyms": ["program"],
      "antonyms": ["hardware"],
      "examples": [
        {
          "en": "You need to install new software on your computer.",
          "zh": "你需要在电脑上安装新软件。",
          "zh_hant": "你需要在電腦上安裝新軟體。"
        }
      ]
    }
  ],
  "level": "A2",
  "exam_tags": ["gk", "cet4", "cet6", "ky"],
  "kid_safe": true,
  "game_ok": true,
  "confidence": "high",
  "review_status": "agreed"
}
```

> **两岸用词真校对，而非简单转字**：例如 `window` 的计算机义项例句 *"Close the window and save your file."*，简体为「关闭窗口并保存文件。」，台湾繁体校对为「關閉視窗並儲存檔案。」；而普通义项的「窗户」不会像 OpenCC `s2twp` 那样被误伤成「視窗」。

---

## 10 秒快速上手

### 1. 直接下载预构建发布包（推荐）

前往 **[GitHub Releases](https://github.com/greypapl/open-learner-dict/releases)** 按需下载（均附 `MANIFEST.json` 与 SHA-256 校验）：

- `open-learner-dict-0.10.0-sqlite.zip`（27.5 MB）—— 应用/后端直连，开箱查词
- `open-learner-dict-0.10.0-jsonl.zip`（14.8 MB）—— 完整结构化数据，配合 [schema/](schema/) 做二次处理
- `open-learner-dict-0.10.0-csv.zip`（11.9 MB）—— UTF-8 BOM CSV，Excel / Pandas 直开
- `open-learner-dict-0.10.0-wordlists.zip`（0.8 MB）—— 12 份现成纯词表（CEFR A1–C2、中考/高考/四六级/考研、儿童与游戏安全词表）

或本地从源码重构建：`python -X utf8 -I scripts/release.py --version 0.10.0`（校验：`python -X utf8 -I scripts/make_schema.py`）。

### 2. 一条 SQL 查任何词（原形、变形、短语、搭配、专名）

```sql
-- 任意写法先查统一 lookup 表（key 一律小写）
SELECT layer, id FROM lookup WHERE key = 'went';       -- → inflection, go 的 id
SELECT layer, id FROM lookup WHERE key = 'decision';   -- → core, w000781

-- 读取词条、义项与例句
SELECT e.word, e.ipa_us, e.level, s.pos, s.zh, s.zh_hant, ex.en, ex.zh
FROM entries e
JOIN senses s ON s.entry_id = e.id
LEFT JOIN examples ex ON ex.sense_id = s.sense_id
WHERE e.id = 'w000781'
ORDER BY s.idx;
```

完整字段说明、表结构与更多查询示例见 **[docs/DATA.md](docs/DATA.md)**。

---

## 质量工程与透明评估

- **三步流水线**：主词典 86,851 词全部经过「写手 → 独立审核 → 第三方更强模型仲裁」闭环，不靠单次生成直接交付。
- **稳定 ID 与勘误机制**：每个词条（`w000001`）与义项（`w000001.1`）跨版本稳定；发现错误可在 Issue 中附带 ID，写入 [data/errata.jsonl](data/errata.jsonl) 后每次发版自动生效。
- **公开独立抽检**：所有抽检脚本（`scripts/audit.py`）、评分标准与 2,100 条抽检报告全文公开在 [reports/quality-0.10.0.md](reports/quality-0.10.0.md)。

---

## 适用场景与后续规划

- **开箱适用**：词典与背词 App、浏览器划词翻译插件、拼词/接龙类文字游戏（内置 `game_ok` / `kid_safe`）、Anki 制卡与教学资料、NLP / RAG 词法分析。
- **下一步路线图（通往 v1.0.0）**：按词性拆分同形异音词音标（如 `record` / `present`）、补齐短语层 1.3 万条例句、导出 MDX / Anki 格式包、可选音频方案。

---

## 许可与致谢

- **数据**：[CC BY-SA 4.0](LICENSE-DATA)（署名、相同方式共享，允许商用）
- **代码**：[MIT](LICENSE)
- **第三方致谢**：词频、美音音标、考试标签与字形转换基于 wordfreq、CMUdict、ECDICT（仅用词头/变形/考试标签，**不含其释义**）与 OpenCC，详见 [NOTICE.md](NOTICE.md)。
- **文档索引**：数据规范 [docs/DATA.md](docs/DATA.md) · 架构设计 [SPEC.md](SPEC.md) · 项目进展 [STATUS.md](STATUS.md)
