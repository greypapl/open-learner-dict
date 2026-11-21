# 例句繁體校對 · hant-ex-v1

Example sentences of an English–Chinese learner's dictionary were translated into Mainland Simplified Chinese and then converted to Traditional Chinese with OpenCC (character mode `s2tw`, plus a small table of Taiwan terms). Your job: make each Traditional sentence read as correct, natural **Taiwan Mandarin (臺灣華語)**, the way a Taiwanese textbook editor would write it. You must know Taiwan usage well.

Input lines in {INPUT}: `key | 简体原句 | 繁體（自動轉換）`

**Write to {OUTPUT} only the lines whose 繁體 needs a change**, as `key | corrected 繁體 sentence` (the whole sentence). Copy the key exactly. Most lines are already fine; typically a few to ten lines per hundred need changes. Read every line — do not use scripts to decide.

## What to fix
1. **Wrong character from conversion** (OpenCC splits words wrongly or picks the wrong one of several traditional characters). Check every one of these carefully against the meaning in context:
   - 曆/歷（歷史、經歷；曆 only for calendars）、游/遊（游泳、上游；遊 for travel/play）、個/箇（一個, never 一箇）、裡/里（裡面、湯裡；里 for 英里/公里/鄰里）
   - 髮/發、麵/面、乾/幹/干、隻/只、鐘/鍾、週/周、係/系/繫、誌/志、佈/布、鬆/松、準/准、錶/表、菸/煙、製/制、盃/杯、蹟/跡、鍊/煉/鏈、臟/髒、嚐/嘗、盪/蕩、藉/借、瞭/了、後/后、著/着、於/于、餘/余、捲/卷、衝/沖、穀/谷、醜/丑、範/范、彙/匯、闆/板、鬥/斗、薑/姜、蘋/苹
2. **Mainland vocabulary where Taiwan clearly differs**: 視頻→影片, 質量(quality)→品質, 信息→資訊/訊息, 網絡→網路, 軟件→軟體, 打印→列印, 出租車→計程車, 公交車→公車, 自行車→腳踏車, 地鐵→捷運 (only for a Taiwan-style city metro in general use; 地鐵 is fine for London/New York), 發動機→引擎, 土豆→馬鈴薯, 酸奶→優格, 冰激凌→冰淇淋, 幼兒園→幼稚園, 菠蘿→鳳梨, 三文魚→鮭魚, 方便麵→泡麵, 樂隊→樂團 (pop/rock band), 水平(level of skill)→水準, 博客→部落格, 短信→簡訊, 激光→雷射, 屏幕→螢幕, 鼠標→滑鼠, 盒飯→便當, 塑料→塑膠, 概率→機率, 宇航員→太空人, 打的→搭計程車, 手機 (same), 電腦 (same).
3. **Place and people names**: 悉尼→雪梨, 新西蘭→紐西蘭, 意大利→義大利, 格魯吉亞→喬治亞, 肯尼亞→肯亞, 尼日利亞→奈及利亞, 沙特→沙烏地, 朝鮮→北韓 (the country), 湯姆/安娜 (same), 奧巴馬→歐巴馬 (if a real person ever appears).
4. Taiwan punctuation is the same as the input (full-width ，。？！、「」 or “”) — do not change quotation marks or punctuation style.

## What not to do
- Do not rephrase for style, shorten, or "improve" the translation; do not change correct text.
- Do not change words that are normal in both places (電腦, 手機, 公司, 學校, 老師, 視窗 is wrong for 窗口 meaning a window: keep 窗口/窗戶 as appropriate).
- Keep numbers and any Latin letters (X光, TV) exactly as they are.

## After writing
Run `.venv/Scripts/python -X utf8 -I scripts/hant.py check` and fix format problems in your own file (ignore other files and 未完成). Reply with the number of lines you wrote per file.
