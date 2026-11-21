# 繁體校對 · hant-v1

An English–Chinese dictionary written in Mainland Simplified Chinese was converted to Traditional Chinese with OpenCC (Taiwan phrase mode). OpenCC already handled characters and many common terms (軟體, 滑鼠, 義大利). Your job is to fix what it missed, so the text reads as natural **Taiwan Mandarin (臺灣華語)**. You must know Taiwan usage well; change only what a Taiwanese editor would change.

**Write to the output file only the lines that need a change**, as `key | corrected text`. Copy the key exactly. An empty file is fine. Do not use scripts to decide.

## T files — definitions
Input: `key | English | POS or pattern | 繁體釋義` (several near-synonyms separated by `, `).
Fix, keeping the same number of comma-separated items and the same meaning:
- Mainland-only vocabulary → Taiwan term: 土豆→馬鈴薯, 西紅柿→番茄, 酸奶→優格, 公交車→公車, 出租車→計程車 (if left), 自行車→腳踏車, 地鐵→捷運 (only for a city metro system in general use; keep 地鐵 where both are fine), 視頻→影片, 質量 (meaning quality)→品質 (keep 質量 for physical mass), 博客→部落格, 短信→簡訊, 激光→雷射, 打印→列印, 信息→資訊/訊息, 數據→資料 (data) but 數據 is also used, 網絡→網路, 硬件→硬體, 程序→程式 (program) / 程序 (procedure), 默認→預設, 奶酪→起司/乳酪, 三文魚→鮭魚, 菠蘿→鳳梨, 幼兒園→幼稚園/幼兒園, 冰激凌→冰淇淋, 創可貼→OK繃 is not allowed (no Latin letters) so use 膠布, 宇航員→太空人, 概率→機率, 屏幕→螢幕, 知識產權→智慧財產權, 人工智能→人工智慧, 互聯網→網際網路, 圓珠筆→原子筆, 方便麵→泡麵, 搞→弄 only if unnatural.
- Wrong character choices from conversion (乾/幹/干, 髮/發, 裡/里, 著/着, 臺/台 are both fine).
- Country and place names inside definitions (悉尼→雪梨, 新西蘭→紐西蘭, 沙特→沙烏地, 朝鮮→北韓 where it means the country, 老撾→寮國).
Do **not** rephrase for style, do not change correct text, do not add or remove items.

## N files — proper names
Input: `key | Display | type（說明） | 中文名`. Output the name used in Taiwan media **only when it differs** from the given one:
- people: Obama 奧巴馬→歐巴馬, Trump 特朗普→川普, Kennedy 肯尼迪→甘迺迪, Johnson 約翰遜→強森, Beckham 貝克漢姆→貝克漢, Jordan 喬丹 (same, skip), Reagan 裡根→雷根, Shakespeare 莎士比亞 (same).
- places: Sydney 悉尼→雪梨, New Zealand 新西蘭→紐西蘭, Italy 意大利→義大利, Saudi 沙特→沙烏地, Qatar 卡塔爾→卡達, Kenya 肯尼亞→肯亞, Nigeria 尼日利亞→奈及利亞, Laos 老撾→寮國, Georgia 格魯吉亞→喬治亞, Monaco 摩納哥 (same).
- brands/works/orgs: Mercedes 奔馳→賓士, Lexus 雷克薩斯→凌志, Star Wars 星球大戰→星際大戰, Harry Potter 哈利波特 (same), Nokia 諾基亞 (same), Sony 索尼 (same).
- ordinary given names and surnames: only change when Taiwan has a clearly different established form (John 約翰 same; Johnson 強森; Williams 威廉斯; Smith 史密斯 same; Michael 麥可; David 大衛 same; Peter 彼得 same; Richard 理查; George 喬治 same; Thompson 湯普森 same). If you are not sure Taiwan differs, leave the line out.
Chinese characters only (no Latin letters, no brackets).

## After writing
Run `.venv/Scripts/python -X utf8 -I scripts/hant.py check` and fix format problems in your own files (ignore other files and 未完成). Reply with the number of lines written per file.
