# open-learner-dict

面向中文学习者的开放英汉词库：主词典 8.7 万词，加上冷僻词简释、专名、短语、搭配和变形索引，共约 16.9 万条，全部结构化、可商用。

Open English–Chinese learner's dictionary: 86,851 fully written headwords plus rare-word glosses, proper names, phrases, collocations and an inflection index (about 169,000 entries). Structured data, free to use.

> 当前版本 **v0.10.0（预览版）**。全部内容由 Claude 模型撰写和互相审核，**没有人工校对**。错误率估计见 [reports/quality-0.9.0.md](reports/quality-0.9.0.md)。

## 内容

| 层 | 条数 | 说明 |
|---|---|---|
| 主词典 core | 86,851 词，105,257 个义项 | 中文释义、英文简释、美英音标、音节、词族、CEFR 级别、考试标签、是否适合儿童和游戏 |
| 简释 gloss | 50,983 | 冷僻词的一行中文简释（未审核） |
| 专名 proper | 12,954 | 地名、人名、品牌、机构缩写的中文名（未审核） |
| 短语 phrases | 13,153 | 短语动词、习语、固定短语、分写复合词 |
| 搭配 collocations | 5,016 | make a decision、heavy rain 这类强搭配 |
| 变形索引 inflections | 43,919 | went → go、children → child |
| 例句 examples | 29,034 | 前 1 万常用词和全部 A1–C1 词，每个义项 1 句英文例句 + 简繁译文 |

## 怎么用

1. 生成发布包：`python -X utf8 -I scripts/release.py`，产物在 `release/0.10.0/`（JSONL、CSV、SQLite、纯词表）。
2. 读 [docs/DATA.md](docs/DATA.md)：每个文件、每个字段的含义，以及查词的 SQL 示例。
3. JSON Schema 在 [schema/](schema/)；`python -X utf8 -I scripts/make_schema.py` 会重新生成并校验发布包。

最快的接入方式是直接用 `open-learner-dict.sqlite`：

```sql
SELECT layer, id FROM lookup WHERE key = 'went';   -- → inflection, go 的 id
```

## 特点

- 释义全部从头撰写，没有照抄任何现成词典；义项按现代常用度排序，第一个义项就是最该先学的意思。
- 主词典每条都经过「写手 → 审核 → 有分歧再仲裁」三步；每层都标了可信度，未审核的层不和主词典混在一起。
- 每个词和义项有稳定 ID，方便报错和跨版本对照。
- 简体（大陆用语）和繁体（台湾用语）并列；繁体不是简单转字，常用部分逐条校对过台湾说法和译名。

## 还没有的

罕见词（排名 1 万以后的 C2 词）和短语的例句、同义词和反义词、发音音频。已知问题见质量报告。

## 许可

- 数据：CC BY-SA 4.0（署名、相同方式共享） · 代码：MIT · 第三方来源见 [NOTICE.md](NOTICE.md)
- 本词库最初为「单词接龙」而做。设计文档 [SPEC.md](SPEC.md)，维护记录 [STATUS.md](STATUS.md)。
