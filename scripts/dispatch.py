"""打印填好参数的子 agent 提示词，并打 .started 标记（主会话只需复制给 Agent 工具，不必读任何大文件）。

  python -X utf8 -I scripts/dispatch.py writer B0089 [B0090 …] [--per 2] [--effort low|medium] [--model fable]
      每 --per 批一段提示词（一段派一个 Opus 写手）
  python -X utf8 -I scripts/dispatch.py reviewer B0089 B0090
      一段提示词审 2 批（派一个 Opus 审核）
  python -X utf8 -I scripts/dispatch.py arbiter B0089 B0090 …
      一段提示词仲裁多批（建议攒 10–15 批派一个 Fable）；自动略过无分歧的批次
  加 --dry 只打印不打标记。
"""
import sys, time, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R = 'C:/Users/greypapl/project/整理单词'
RAW = ROOT / 'work' / 'raw'
PY = f'{R}/.venv/Scripts/python -X utf8 -I'
COMMON = ("Do not open any other project files (nothing under sources/ unless stated); no web. "
          "If you need helper scripts, keep them only in your own folder {R}/work/tmp/{tag}/ (other agents run in parallel). "
          "Keep tool output short: do not cat whole files back; read each file once.")


def opt(args, name, default=None):
    if name in args:
        i = args.index(name)
        v = args[i + 1]
        del args[i:i + 2]
        return v
    return default


def mark(stage, b, dry):
    if not dry:
        (RAW / f'{b}.{stage}.started').write_text(str(time.time()))


def writer(bs):
    """一个写手 agent 依次写 bs 中的批次（每批 200 词，各自输出）。"""
    jobs = '\n'.join(f"- {{INPUT}} = {R}/work/batches/{b}.input.jsonl, {{OUTPUT}} = {R}/work/raw/{b}.writer.txt" for b in bs)
    return f"""You are a dictionary writer. Read and follow exactly {R}/prompts/writer.md with {{RULES}} = {R}/prompts/rules.md. Write these batches one after another, each into its own output:
{jobs}
For each batch: write its 200 lines in two chunks of 100 (<B>.writer.part1.txt, part2.txt in work/raw), concatenate them in order into the output with a shell command and delete the parts.
Then run `{PY} {R}/scripts/compact.py expand writer <B>` and `node {R}/scripts/validate.js {R}/work/raw/<B>.writer.jsonl --input {R}/work/batches/<B>.input.jsonl`. Fix every reported problem in the .txt file (edit only the affected lines) and re-run both until they pass, then move on to the next batch.
{COMMON.format(tag=bs[0], R=R)} Final reply: one `done <B> <kept> <skipped>` line per batch."""


def reviewer(bs):
    jobs = '\n'.join(f"- {{INPUT}} = {R}/work/batches/{b}.input.jsonl, {{WRITER_OUTPUT}} = {R}/work/raw/{b}.writer.txt, {{OUTPUT}} = {R}/work/raw/{b}.reviewer.txt" for b in bs)
    checks = ' and '.join(f"`{PY} {R}/scripts/compact.py expand reviewer {b}` + `node {R}/scripts/validate.js {R}/work/raw/{b}.reviewer.jsonl --input {R}/work/batches/{b}.input.jsonl`" for b in bs)
    return f"""You are a dictionary reviewer. Read and follow exactly {R}/prompts/reviewer.md with {{RULES}} = {R}/prompts/rules.md and {{OLD_REF}} = {R}/sources/old-cleaned.csv (large: only Grep specific words, never read it whole). Review these batches one after another, each into its own output:
{jobs}
After each output, run {checks} (for that batch). Fix problems in your `fixed` lines and re-run until they pass. Do not open sources/ecdict.csv.
{COMMON.format(tag='rev-' + bs[0], R=R)} Final reply: one `done <ok> <fix>` line per batch."""


def arbiter(bs):
    jobs = '\n'.join(f"- work/raw/{b}.disputes.txt → work/raw/{b}.arbiter.txt" for b in bs)
    checks = f"`{PY} {R}/scripts/compact.py expand arbiter <B>` then `node {R}/scripts/validate.js {R}/work/raw/<B>.arbiter.jsonl`"
    return f"""You are the final arbiter for a dictionary. Read and follow exactly {R}/prompts/arbiter.md with {{RULES}} = {R}/prompts/rules.md. Files (relative to {R}):
{jobs}
After writing each output, run {checks} and fix problems in your `final` lines until they pass.
{COMMON.format(tag='arb-' + bs[0], R=R)} Final reply: one `done <B> <count>` line per batch."""


if __name__ == '__main__':
    a = sys.argv[1:]
    dry = '--dry' in a
    if dry:
        a.remove('--dry')
    effort, model = opt(a, '--effort'), opt(a, '--model')
    per = int(opt(a, '--per', 1))
    stage, *bs = a
    if stage == 'writer':
        for b in bs:
            mark('writer', b, dry)
            if not dry:
                if effort:
                    (RAW / f'{b}.writer.effort').write_text(effort)
                if model == 'fable':
                    (RAW / f'{b}.writer.model').write_text('claude-fable-5-2')
        for i in range(0, len(bs), per):
            g = bs[i:i + per]
            print(f"===== writer {' '.join(g)} · model={model or 'opus'}" + (f" · effort={effort}" if effort else '') + ' =====')
            print(writer(g), '\n')
    elif stage == 'reviewer':
        for b in bs:
            mark('reviewer', b, dry)
            if not dry:   # 记录同组批次：tick.py 等整组都产出后才算分歧
                (RAW / f'{b}.reviewer.group').write_text(' '.join(bs))
        print(f"===== reviewer {' '.join(bs)} · model=opus =====")
        print(reviewer(bs))
    elif stage == 'arbiter':
        bs = [b for b in bs if (RAW / f'{b}.disputes.txt').exists()]
        if not bs:
            sys.exit('没有需要仲裁的批次（无 disputes.txt）')
        n = sum(len((RAW / f'{b}.disputes.txt').read_text(encoding='utf-8').splitlines()) for b in bs)
        for b in bs:
            mark('arbiter', b, dry)
        print(f"===== arbiter {' '.join(bs)} · {n} 条分歧 · model=fable =====")
        print(arbiter(bs))
