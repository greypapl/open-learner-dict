# 生产流水线运行手册（编排者用）

项目根：`C:/Users/greypapl/project/整理单词`，Python 用 `.venv/Scripts/python -X utf8 -I`。
**手动模式**（2026-11-14 起）：不设定时任务，由维护者决定何时派发。完整步骤与额度经验见 ../STATUS.md。

## 提示词版本
- v3（B0089 起）：`rules.md`（共用规范，紧凑行格式）+ `writer.md` / `reviewer.md` / `arbiter.md`。
- 存档：`writer-v2.md`、`reviewer-v2.md`、`arbiter-v1.md`（B0001–B0088 使用）。

## 派发
子 agent 提示词不再手抄模板，由 `scripts/dispatch.py` 生成（同时打 `.started` 标记）：

| 角色 | 命令 | 模型 | 粒度 |
|---|---|---|---|
| 写手 | `dispatch.py writer <B>… --per 3 --effort low` | opus（effort=low） | 一个 agent 写 3 批 |
| 审核 | `dispatch.py reviewer <5 批>` | opus | 一个 agent 审 5 批 |
| 仲裁 | `dispatch.py arbiter <约 10 批>` | fable | 一个 agent 仲裁约 10 批 |

把打印出的那段提示词原样交给 Agent 工具（model 按上表；写手用了 `--effort` 时 Agent 的 effort 也设成同一值）。
主会话不读词条文件、不 cat 大输出，只看 agent 的一行 `done …` 回复和 status.py。

## 闸门与收尾
- 每个 agent 完成后跑 `scripts/tick.py --upto <本轮末批>`：自动校验、算分歧、合并，并给出可派的下一组。
- 5 小时窗口 ≥ 90% 或本周全部模型 ≥ 95% → 不派新 agent。
- 并发：写手 ≤ 5，在途总数 ≤ 10。
- 审核完成后：`pipeline.py disputes <B>…`；0 分歧或仲裁完成后：`pipeline.py merge <B>…`。
- 每累计合并 50 批，随机抽 30 条最终词条自查（义项、排序、音标）；发现系统性问题就停下。

## 已知问题（发布前处理）
- 连字符词（easy-going、long-range、phone-in）的 wordfreq 频率偏高，最终排名需降权（例如取各部分 zipf 最小值再减 1）。
- 连字符词的 syllables 有时未切分，发布脚本按连字符两侧分别处理，不必返工。
