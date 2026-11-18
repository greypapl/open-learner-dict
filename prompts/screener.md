# 初筛提示词 · prompt_ver = screener-v1

你在为英汉学习者词典做**收词初筛**：只判断每个候选是否值得收为词条，不写释义。
凭你自己的语言知识判断，不要上网，不要查阅其他文件。

## 输入

`{INPUT}`：TSV，每行 `id<TAB>word<TAB>hint`。hint 可能为空，或包含：
- `proper` 首字母大写词；`abbr` 全大写缩写
- `infl-of:X` 来源数据认为它是 X 的屈折形式
- `stem?:X` 去掉词尾后 X 也是候选，可能是屈折形式

## 判定（每行一个代码）

收录：
- `K1`：普通词汇。受过教育的成年人在新闻、书籍、日常、网络中可能遇到的词（含常见派生词、常见俚语/新词）。
- `K2`：真实存在但罕见或专业的词（医学、生物、化学、法律术语，古旧词，罕见派生词）。

跳过：
- `S not-lemma`：纯屈折形式（复数、过去式、-ing、第三人称、比较级），且没有独立于原形的常用词义。有独立词义的保留（left、data、news、building、feeling）。
- `S proper-out-of-scope`：人名、地名、城市、州、机构、品牌等专有名词（含小写形式的人名如 dan、johnson）。**保留**：星期、月份、国家、语言、民族/国籍形容词、重大节日、Mr/Mrs/Dr。
- `S abbr-rare`：非大众常用的缩写。
- `S junk`：拼写错误（postpon、thril、focuss）、错误切分的残片（forcep、doldrum 除非确有此词）、无意义字母组合、你无法确认存在的词。
- `S not-english`：未被英语吸收的外语词。
- `S variant`：只是另一个更常见拼写的罕见异体，且没有独立意义（例：enamor 不算，它是美式正拼；focussed 类错误拼写归 junk）。

**拿不准时：真实性存疑 → `S junk`；屈折还是独立词存疑 → 收录（K1/K2），交给后续编纂者判断。**

## 输出

写到 `{OUTPUT}`：TSV，每个输入行恰好一行，顺序一致：
```
w001234	K1
w001235	K2
w001236	S	junk
```
不要表头、不要其他文字。写完后运行：
`node C:/Users/greypapl/project/整理单词/scripts/check_screen.js {INPUT} {OUTPUT}`
有错就修到通过。最后回复一行：`done <K1数> <K2数> <S数>`。
