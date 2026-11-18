# open-learner-dict 规格（SPEC）

> 版本：spec v1.0（2026-11-14 定稿）。本文件是项目唯一的设计依据；改动需同步更新版本号。

## 1. 定位

面向中文学习者的英汉词库。卖点是**释义干净、义项按现代常用度排序**，App、游戏、词典软件可直接使用。
不与 ECDICT 拼规模。「权威」靠公开、可复现的质量证据来挣，不靠自称。

- 数据协议：**CC BY-SA 4.0**；脚本代码：MIT。
- 全部完成后再公开。README 只用一行注明「用于单词接龙」。

## 2. 数据来源

| 内容 | 来源 | 备注 |
|---|---|---|
| 词头候选 | ECDICT 词头 | 事实数据，仅用词头 |
| 排名 | wordfreq（CC BY-SA 4.0）重排 | 取前 100,000 个原形词 |
| 音标 / 音节 / 重音 | CMUdict（BSD-2） → IPA | 英音与缺失由 Opus 补，标 `confidence=low` |
| 屈折形式 | ECDICT `exchange` 字段 | 事实数据 |
| 考试标签 | ECDICT `tag` 字段（zk/gk/cet4/cet6/ky），对照官方大纲 | 雅思/托福无官方词表，不打 |
| 释义及其余全部文本 | **Opus 从零撰写** | 写手**永远看不到** ECDICT 释义 |
| 繁体 | OpenCC（s2twp） | 处理台湾用词 |

## 3. 收词范围

- 以原形（lemma）为主；屈折变化放 `inflections`。
- 专有名词只收进入普通词汇的：星期、月份、国家、语言名。
- 缩写/首字母词只收高频的。
- 不收多词词组（词组进扩展层短语库）。

## 4. 核心层词条结构（10 万词全覆盖，v1.0 必需）

```jsonc
{
  "id": "w000123",                 // 稳定 ID，永不复用
  "word": "happy",
  "rank": 123,                     // wordfreq 重排后名次
  "ipa_uk": "ˈhæpi", "ipa_us": "ˈhæpi",
  "syllables": "hap·py", "stress": [1, 0],
  "senses": [
    {
      "sense_id": "w000123.1",     // 稳定义项 ID
      "pos": "adj.",
      "zh": "快乐的, 高兴的, 幸福的",
      "zh_hant": "快樂的, 高興的, 幸福的",
      "en_short": "feeling or showing pleasure",
      "register": [],              // formal|informal|slang|dated|uk|us|offensive-mild|offensive-strong|domain:医 ...
      "synonyms": [], "antonyms": [],    // 扩展层填充
      "examples": []                     // 扩展层填充（仅前 3 万）
    }
  ],
  "inflections": {"comparative": "happier", "superlative": "happiest"},
  "spelling_variants": [],
  "word_family": ["happiness", "unhappy", "happily"],
  "affixes": [],                   // 严格版：只拆标准前后缀，不讲词源故事
  "level": "A1",                   // CEFR，Opus 估计值
  "level_estimated": true,
  "exam_tags": ["zk", "gk", "cet4"],
  "offensive": null,               // null | "mild" | "strong"
  "kid_safe": true,
  "game_ok": true,                 // 排除缩写、专有名词、带连字符/空格/撇号
  "confidence": "high",            // high | low
  "review_status": "agreed",       // agreed | arbitrated | disputed
  "meta": {"model": "...", "prompt_ver": "...", "review": "..."}
}
```

## 5. 释义风格规范（写手与审核共用）

- 每个义项中文 2–4 个近义词，英文逗号+空格分隔，不写解释性长句。
- 义项按**现代英语使用频率**排序，不按词源或历史。
- 每个词性最多 3 条义项，全词最多 6 条。
- 词性标记统一：`n. v. adj. adv. prep. conj. pron. det. int. num. aux. abbr.`（不区分 vt/vi）。
- `en_short` ≤ 12 个英文单词。
- 只有专业义的罕见词照实写，并在 `register` 标领域（如 `domain:医`）。
- 宁可少写一个义项，不要写错。

## 6. 扩展层（核心层完成后依次进行）

1. 例句：前 3 万词，每义项 1 句中英双语。
2. 短语库：词组、短语动词、搭配，1–2 万条，挂在中心词下。
3. 同义/反义词（每义项 ≤3）与易混词表。

## 7. 生产流程

1. **数据准备**：词头 + wordfreq 排名 + CMUdict + exchange + tag → `work/headwords.jsonl`。
2. **写手**：Opus 子 agent，每批 200 词。
3. **规则检查**：`scripts/validate.js`（词性合法、条数/长度上限、字段齐全、屏蔽词）。
4. **审核**：另一个 Opus 子 agent。可参考旧版清理成果，**只用来查漏，不准照抄**。
5. **仲裁**：写手与审核有分歧 → Fable。
6. **仍有分歧**：只保留双方都同意的义项，标 `confidence=low`、`review_status=disputed`。
7. 全程无人工审核；唯一例外：开跑前 200 词分层试点，由维护者过目一次。
8. 每轮 5 个写手并行（约 1000 词），落盘，可断点续跑。先跑 1–2 轮观察订阅用量。

## 8. 质量证据

- 每个里程碑由 Fable 独立抽检 500 条，按排名分段公布错误率。
- 公布 disputed 与 `confidence=low` 占比。
- 每条 `meta` 记录模型、提示词版本、审核结果。
- 词与义项稳定 ID + GitHub Issue 勘误模板。
- 与 ECDICT 做覆盖率对比（只比有没有漏掉常用义项，不复制文字）。

## 9. 发布格式（全部由脚本从主数据生成）

- 主数据：`data/<首字母>.jsonl`
- CSV、SQLite、完整 JSON
- MDX、StarDict（欧路、GoldenDict、MDict）
- Anki 卡组（按考试/等级拆分）
- 按考试标签拆分的纯词表（txt）
- JSON Schema + 字段文档（语义化版本）
- npm / Python 包（v1.0 之后）

## 10. 明确放弃

发音音频、课本单元映射、10 万名以后的词、Scrabble 官方词表对标、词源故事式的词根词缀。

## 11. 里程碑

1. 试点（200 词分层）
2. 核心层：1 万 → 3 万 → 6 万 → 10 万
3. 扩展层：例句 → 短语库 → 同反义词与易混词
4. 生成全部发布格式与质量报告，公开
