// 初筛输出检查：node scripts/check_screen.js <input.tsv> <output.tsv>
const fs = require('fs')
const REASONS = new Set(['not-lemma', 'proper-out-of-scope', 'abbr-rare', 'junk', 'not-english', 'variant'])
const lines = f => fs.readFileSync(f, 'utf8').replace(/^﻿/, '').split(/\r?\n/).filter(l => l.trim())
const [inp, out] = process.argv.slice(2).map(lines)
const errs = []
if (inp.length !== out.length) errs.push(`行数 ${out.length} ≠ 输入 ${inp.length}`)
inp.forEach((l, i) => {
  const id = l.split('\t')[0]
  const o = (out[i] || '').split('\t')
  if (o[0] !== id) errs.push(`第${i + 1}行 id 对不上: 期望 ${id}，实际 ${o[0]}`)
  else if (o[1] === 'S') { if (!REASONS.has(o[2])) errs.push(`${id}: 跳过原因非法 ${o[2]}`) }
  else if (o[1] !== 'K1' && o[1] !== 'K2') errs.push(`${id}: 代码非法 ${o[1]}`)
})
if (errs.length) { console.log(errs.slice(0, 30).join('\n') + `\n共 ${errs.length} 处问题`); process.exit(1) }
console.log(`✓ ${inp.length} 行全部通过`)
