// 规则检查：校验写手格式的词条（写手输出 / 审核 fixed / 仲裁 final）
// 用法: node scripts/validate.js <file.jsonl> [--input <batch.input.jsonl>]
//   --input 时额外检查：一一对应、顺序一致、id/word 与输入相符
// 退出码: 0 全部通过；1 有错误（逐条打印）
const fs = require('fs')
const path = require('path')

const POS = new Set(['n.', 'v.', 'adj.', 'adv.', 'prep.', 'conj.', 'pron.', 'det.', 'int.', 'num.', 'aux.', 'abbr.'])
const REG = /^(formal|informal|slang|dated|literary|uk|us|offensive-mild|offensive-strong|domain:(医学|解剖|药学|生物|植物|动物|化学|物理|数学|天文|地质|地理|气象|计算机|电子|机械|建筑|军事|航海|航空|法律|经济|金融|商业|政治|宗教|哲学|语言|文学|音乐|美术|体育|烹饪|农业|心理|教育|历史|摄影|纺织|印刷|矿业|统计|逻辑|神话))$/
const LEVEL = new Set(['A1', 'A2', 'B1', 'B2', 'C1', 'C2'])
const SKIP = new Set(['not-lemma', 'proper-out-of-scope', 'abbr-rare', 'junk', 'not-english', 'too-rare'])
const BLOCK = new Set(fs.readFileSync(path.join(__dirname, 'blocklist.txt'), 'utf8')
  .split(/\r?\n/).map(s => s.trim()).filter(s => s && !s.startsWith('#')))

function readJsonl(f) {
  return fs.readFileSync(f, 'utf8').replace(/^﻿/, '').split(/\r?\n/).filter(l => l.trim())
    .map((l, i) => { try { return JSON.parse(l) } catch (e) { return { __bad: `第${i + 1}行不是合法 JSON` } } })
}

// 从审核/仲裁行里取出词条
function entryOf(row) {
  if (row.final) return row.final
  if (row.fixed) return row.fixed
  return row
}

function checkEntry(e) {
  const err = []
  if (!e.id || !e.word) err.push('缺 id/word')
  if (e.skip !== undefined && e.skip !== null) {
    if (!SKIP.has(e.skip)) err.push(`skip 原因非法: ${e.skip}`)
    return err
  }
  if (!Array.isArray(e.senses) || e.senses.length === 0) return err.concat('senses 为空')
  if (e.senses.length > 6) err.push(`义项 ${e.senses.length} > 6`)
  const perPos = {}
  for (const s of e.senses) {
    if (!POS.has(s.pos)) err.push(`词性非法: ${s.pos}`)
    perPos[s.pos] = (perPos[s.pos] || 0) + 1
    const zh = (s.zh || '').split(', ').filter(Boolean)
    if (zh.length < 1 || zh.length > 4) err.push(`zh 近义词数 ${zh.length}: ${s.zh}`)
    if (/[;；。（）()]/.test(s.zh || '')) err.push(`zh 含禁用标点: ${s.zh}`)
    if (zh.some(z => z.length > 12)) err.push(`zh 单项过长: ${s.zh}`)
    if (/[\[\]]/.test(s.en_short || '')) err.push(`en_short 含方括号（标签未解析）: ${s.en_short}`)
    const n = (s.en_short || '').trim().split(/\s+/).filter(Boolean).length
    if (n === 0 || n > 12) err.push(`en_short 词数 ${n}`)
    for (const r of s.register || []) if (!REG.test(r)) err.push(`register 非法: ${r}`)
  }
  for (const [p, n] of Object.entries(perPos)) if (n > 3) err.push(`${p} 义项 ${n} > 3`)
  if (!e.ipa_us || !e.ipa_uk) err.push('缺音标')
  if (!['cmu', 'model'].includes(e.ipa_source)) err.push(`ipa_source 非法: ${e.ipa_source}`)
  if (/[\/\[\]]/.test((e.ipa_us || '') + (e.ipa_uk || ''))) err.push('音标含斜杠/方括号')
  if (((e.ipa_us || '').match(/ˈ/g) || []).length > 1) err.push(`ipa_us 双主重音: ${e.ipa_us}`)
  if (!e.syllables || e.syllables.replace(/·/g, '').toLowerCase() !== e.word.toLowerCase())
    err.push(`syllables 与词不符: ${e.syllables}`)
  for (const k of ['word_family', 'affixes', 'spelling_variants'])
    if (!Array.isArray(e[k])) err.push(`${k} 不是数组`)
  if ((e.word_family || []).length > 6) err.push('word_family > 6')
  for (const a of e.affixes || []) if (!/^(-[a-z]+|[a-z]+-)$/.test(a)) err.push(`affix 格式: ${a}`)
  if (!LEVEL.has(e.level)) err.push(`level 非法: ${e.level}`)
  if (![null, 'mild', 'strong'].includes(e.offensive)) err.push(`offensive 非法: ${e.offensive}`)
  if (typeof e.kid_safe !== 'boolean') err.push('kid_safe 不是布尔')
  if (e.offensive && e.kid_safe) err.push('冒犯词却 kid_safe=true')
  if (BLOCK.has(e.word.toLowerCase()) && e.kid_safe) err.push('屏蔽词却 kid_safe=true')
  if (!['high', 'low'].includes(e.confidence)) err.push(`confidence 非法: ${e.confidence}`)
  return err
}

function main() {
  const args = process.argv.slice(2)
  const file = args[0]
  const ii = args.indexOf('--input')
  const rows = readJsonl(file)
  let bad = 0
  const report = (id, msgs) => { bad++; console.log(`✗ ${id}: ${msgs.join('；')}`) }
  if (ii > 0) {
    const inp = readJsonl(args[ii + 1])
    if (inp.length !== rows.length) report('(批次)', [`行数 ${rows.length} ≠ 输入 ${inp.length}`])
    inp.forEach((x, i) => {
      const r = rows[i]
      if (r && (r.id !== x.id || r.word !== x.word)) report(x.id, [`第${i + 1}行对不上: ${r.id}/${r.word}`])
    })
  }
  for (const r of rows) {
    if (r.__bad) { report('(解析)', [r.__bad]); continue }
    if (r.verdict === 'ok') continue
    const msgs = checkEntry(entryOf(r))
    if (msgs.length) report(r.id, msgs)
  }
  console.log(bad ? `共 ${bad} 处问题 / ${rows.length} 行` : `✓ ${rows.length} 行全部通过`)
  process.exit(bad ? 1 : 0)
}

if (require.main === module) main()
module.exports = { checkEntry }
