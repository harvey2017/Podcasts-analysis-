#!/usr/bin/env python3
import json, os

base = "/Users/linqian/Desktop/Gooaye podcasts"

eps = {}
for ep in ["ep660","ep661","ep662","ep663","ep664","ep665"]:
    with open(f"{base}/{ep}_analysis.json", encoding="utf-8") as f:
        eps[ep] = json.load(f)

def sentiment_class(s):
    m = {"bullish":"s-bull","watchful":"s-watch","neutral":"s-neu","bearish":"s-bear","neutral-bullish":"s-nbull"}
    return m.get(s, "s-neu")

def sentiment_label(s):
    m = {"bullish":"看多","watchful":"觀望","neutral":"中立","bearish":"看空","neutral-bullish":"偏多"}
    return m.get(s, s)

def action_class(a):
    if any(x in a for x in ["買","加碼"]): return "a-buy"
    if any(x in a for x in ["出脫","賣","降低"]): return "a-sell"
    if any(x in a for x in ["觀","注意","計劃","業績"]): return "a-watch"
    return "a-hold"

def action_label(a): return a

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def render_ep(ep):
    d = eps[ep]
    parts = []
    parts.append(f'<div class="ep-header">'
        f'<div class="ep-num">{esc(d["episode"])}</div>'
        f'<h2>{esc(d["title"])}</h2>'
        f'<div class="meta">📅 {esc(d["date"])} &nbsp;·&nbsp; ⏱ {esc(str(d["durationMin"]))} 分鐘 &nbsp;·&nbsp; 👤 {esc(d["host"])}</div>'
        f'</div>')

    # Summary
    parts.append('<div class="section"><div class="sec-title">📝 集數摘要</div>'
        f'<div class="summary-box">{esc(d["summary"])}</div></div>')

    # News
    news_html = ""
    for n in d["news"]:
        news_html += (f'<div class="card">'
            f'<div class="news-title">{esc(n["title"])}</div>'
            f'<div class="news-meta"><span class="badge b-cat">{esc(n["category"])}</span>'
            f'<span class="badge b-ref">⏱ {esc(n["sourceRef"])}</span></div>'
            f'<div class="news-event">{esc(n["event"])}</div>'
            f'<div class="blockquote">{esc(n["opinion"])}</div>'
            f'</div>')
    parts.append(f'<div class="section"><div class="sec-title">📰 新聞事件（{len(d["news"])} 則）</div>{news_html}</div>')

    # Host Disclosure
    disc_html = ""
    for disc in d["hostDisclosure"]:
        ac = action_class(disc["action"])
        disc_html += (f'<div class="card">'
            f'<span class="badge {ac}">{esc(disc["action"])}</span>'
            f'<div class="disc-asset">{esc(disc["asset"])}</div>'
            f'<div class="blockquote-purple">「{esc(disc["quote"])}」</div>'
            f'<div class="disc-status">📌 {esc(disc["status"])}</div>'
            f'</div>')
    parts.append(f'<div class="section"><div class="sec-title">⭐ 主持人持倉揭露（{len(d["hostDisclosure"])} 則）</div>{disc_html}</div>')

    # Stock Analysis
    stock_html = ""
    for s in d["stockAnalysis"]:
        sc = sentiment_class(s["sentiment"])
        sl = sentiment_label(s["sentiment"])
        tickers = "".join(f'<span class="ticker">{esc(t)}</span>' for t in (s.get("tickers") or []))
        owned = '<span class="badge b-owned">★ 持有</span>' if s.get("hostOwned") else ""
        stock_html += (f'<div class="card">'
            f'<div class="stock-hdr">'
            f'<div class="stock-name">{esc(s["name"])}</div>'
            f'<div class="stock-badges"><span class="badge {sc}">{sl}</span>{owned}</div>'
            f'</div>'
            f'<div class="tickers">{tickers}</div>'
            f'<div class="risk-line">⚠ 風險：{esc(str(s.get("risk","")))}</div>'
            f'<div class="analysis-text">{esc(s["analysis"])}</div>'
            f'</div>')
    parts.append(f'<div class="section"><div class="sec-title">📊 個股/族群分析（{len(d["stockAnalysis"])} 則）</div>{stock_html}</div>')

    # QA
    qa_html = ""
    for q in d["qa"]:
        pts = "".join(f'<li>{esc(p)}</li>' for p in q["answerPoints"])
        qa_html += (f'<div class="card">'
            f'<div class="qa-sender">@ {esc(q["sender"])}</div>'
            f'<div class="qa-q">{esc(q["question"])}</div>'
            f'<ul class="qa-pts">{pts}</ul>'
            f'<div class="blockquote">{esc(q["keyTakeaway"])}</div>'
            f'</div>')
    parts.append(f'<div class="section"><div class="sec-title">💬 聽眾問答（{len(d["qa"])} 則）</div>{qa_html}</div>')

    return "\n".join(parts)

TREND_HTML = """
<div class="section">
  <div class="sec-title">🔥 被動元件超主題：六集演進時間軸</div>
  <div class="card">
    <div class="trend-timeline">
      <div class="trow"><span class="ep-tag">EP660</span><div class="ttext">全球被動元件同步噴發（日/美/台）；MLCC 排擠效應出現；AI 高規格 47μF 嚴重缺貨；孟公確認「不應該低估這個題材」。</div></div>
      <div class="trow"><span class="ep-tag">EP661</span><div class="ttext">台灣被動元件正式追上國際；鋁電容深度剖析（立隆電、金山電、裕邦 vs 日本 Nichicon/NipponChemical）；Power 廠直接包產能是先行確認信號。</div></div>
      <div class="trow"><span class="ep-tag">EP662</span><div class="ttext">Panasonic SPCAP 確認漲價 30%（六月初生效）；Rohm 漲價信即將落地；電阻同期也漲 30%；採購開始在現貨市場掃貨。</div></div>
      <div class="trow"><span class="ep-tag">EP663</span><div class="ttext">漲價信正式落地（選擇性對部分客戶）；蜜旺時通路商公開確認斷供；2018 超周期類比（國巨毛利 60%+）提出；廠商保守擴產是多頭持久的關鍵。</div></div>
      <div class="trow"><span class="ep-tag">EP664</span><div class="ttext">全線漲停：MLCC、鋁電容、電感、電阻、通路商齊噴；中國江海股份飆漲；日本 Chemical 廠單日漲超 10%；NVIDIA 產能包場光通訊雷射策略確認。</div></div>
      <div class="trow"><span class="ep-tag">EP665</span><div class="ttext">國巨法說確認：特規品稼動率 90%、標準品 80%+、BBR Ratio 持續提升；孟公形容「整組做壞掉，射個滿臉完全看不懂」；每次假摔後又繼續噴出去。</div></div>
    </div>
    <div class="trend-conclusion">結論：被動元件是六集中唯一持續加速的核心主題，從外圍訊號→漲價確認→斷供確認→全線漲停→法說驗證，每集都有新的里程碑。孟公持倉全程持有並多次加碼，是其最重要的單一部位。</div>
  </div>
</div>

<div class="section">
  <div class="sec-title">🔄 老 AI 族群資金輪動弧線</div>
  <div class="card">
    <div class="trend-timeline">
      <div class="trow"><span class="ep-tag">EP660</span><div class="ttext">成熟製程/消費 IC 族群輪動觀察：世界先進、GlobalFoundries、環球晶、瑞昱、聯詠走強，補庫存假說提出。</div></div>
      <div class="trow"><span class="ep-tag">EP661</span><div class="ttext">投信增持台積電上限放寬確認，需 2-3 個月修公開說明書；中小股籌碼面承壓預警；孟公調整為高低配（台積電＋聯發科 核心 ＋ 被動元件）。</div></div>
      <div class="trow"><span class="ep-tag">EP662</span><div class="ttext">禮拜五大跌，老 AI 摔最重，主因毛利率短期承壓；孟公不減碼反而在跌停板買進；「太弱留強」心法：回檔後最快站回的就是下一波主流。</div></div>
      <div class="trow"><span class="ep-tag">EP663</span><div class="ttext">APMemory 復活案例說明老 AI 故事未結束；資金輪動中的被動元件族群強勢；孟公多個標的進入處置股，盤中無法操作。</div></div>
      <div class="trow"><span class="ep-tag">EP664</span><div class="ttext">老 AI 多頭確立，Anthropic 轉獲利打臉泡沫論，Google TPU Cluster 外銷比 3:1 超預期；資金面持續確認 AI 硬體投資不縮減。</div></div>
      <div class="trow"><span class="ep-tag">EP665</span><div class="ttext">機器人族群與載板繼續強勢；SpaceX IPO 成為下一個資金目標；衛星相關已出脫（賺到魚頭），計劃買進 SpaceX 並降低 Tesla。</div></div>
    </div>
    <div class="trend-conclusion">結論：孟公操作邏輯從「等 AI 第一階軟化才轉第二階」（EP660）演變為「高低配同時佈局」（EP661起），並在 EP662 用跌停加碼驗證信念；到 EP665 已看向 SpaceX 的新主題。</div>
  </div>
</div>

<div class="section">
  <div class="sec-title">🚀 新主題：SpaceX IPO ＆ 軌道 AI DataCenter（EP665 首次登場）</div>
  <div class="card">
    <p style="color:#cbd5e0;line-height:1.8;margin-bottom:12px;">EP665 是六集中最重要的主題轉換點。孟公提出全新的投資框架：</p>
    <div class="trend-timeline">
      <div class="trow"><span class="ep-tag">短期</span><div class="ttext">Starlink = 印鈔機，現金流充足，IPO 估值支撐強。</div></div>
      <div class="trow"><span class="ep-tag">長期</span><div class="ttext">軌道 AI DataCenter：衛星上放伺服器做運算，太陽能解決能源問題，輻射散熱解決熱管理問題。</div></div>
      <div class="trow"><span class="ep-tag">供應鏈</span><div class="ttext">散熱族群（目前台股表現不佳但孟公看好）、大片 Carrier Board、太陽能板；衛星 Dish/Router PCBA 已過期，方向轉向軌道算力基礎設施。</div></div>
      <div class="trow"><span class="ep-tag">操作</span><div class="ttext">計劃 IPO 後先卡一半倉位，降低 Tesla 持股轉向 SpaceX，繼續押注馬斯克整體故事。</div></div>
    </div>
    <div class="trend-conclusion">孟公認為現在聚焦軌道算力故事的人還很少，大家還停留在 Starlink 地面業務，這正是早期布局的時機窗口。類比機器人族群邏輯：今年 2%、明年 10% 就是 5 倍成長，題材先行。</div>
  </div>
</div>

<div class="section">
  <div class="sec-title">📈 市場情緒弧線</div>
  <div class="arc-grid">
    <div class="arc-card"><div class="arc-ep">EP660</div><div class="arc-mood" style="color:#fbd38d;">謹慎/尖末期</div><div class="arc-date">2026-05-09</div><div class="arc-desc">進入尖末期模式，拒絕朋友問股</div></div>
    <div class="arc-card"><div class="arc-ep">EP661</div><div class="arc-mood" style="color:#9ae6b4;">高低配樂觀</div><div class="arc-date">2026-05-13</div><div class="arc-desc">台中旅遊，紅酒入坑，策略清晰</div></div>
    <div class="arc-card"><div class="arc-ep">EP662</div><div class="arc-mood" style="color:#fbd38d;">逢跌加碼</div><div class="arc-date">2026-05-16</div><div class="arc-desc">安哥故事，禮拜五跌停買進</div></div>
    <div class="arc-card"><div class="arc-ep">EP663</div><div class="arc-mood" style="color:#9ae6b4;">強勢/達標</div><div class="arc-date">2026-05-20</div><div class="arc-desc">78kg 達標！處置股滿倉，漲停鎖住</div></div>
    <div class="arc-card"><div class="arc-ep">EP664</div><div class="arc-mood" style="color:#9ae6b4;">5月新高</div><div class="arc-date">2026-05-23</div><div class="arc-desc">全線漲停，績效超越4月，羅曼尼康帝</div></div>
    <div class="arc-card"><div class="arc-ep">EP665</div><div class="arc-mood" style="color:#90cdf4;">整組做壞掉</div><div class="arc-date">2026-05-27</div><div class="arc-desc">諾亞絕對音感，SpaceX 新主題登場</div></div>
  </div>
</div>

<div class="section">
  <div class="sec-title">📊 跨集個股出現次數與情緒矩陣</div>
  <div class="card" style="overflow-x:auto;">
    <table class="matrix-table">
      <tr><th>標的/族群</th><th>EP660</th><th>EP661</th><th>EP662</th><th>EP663</th><th>EP664</th><th>EP665</th><th>孟公持有</th></tr>
      <tr><td>被動元件族群</td><td class="m-bull">看多</td><td class="m-bull">看多</td><td class="m-bull">看多</td><td class="m-bull">看多</td><td class="m-bull">看多</td><td class="m-bull">看多</td><td class="m-own">✓</td></tr>
      <tr><td>台積電</td><td class="m-bull">看多</td><td class="m-bull">看多</td><td class="m-bull">看多</td><td class="m-bull">看多</td><td class="m-bull">看多</td><td class="m-bull">看多</td><td class="m-own">✓</td></tr>
      <tr><td>聯發科</td><td class="m-bull">看多</td><td class="m-bull">看多</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-own">✓</td></tr>
      <tr><td>NVIDIA</td><td class="m-bull">看多</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-watch">觀望</td><td class="m-na">—</td><td class="m-na">—</td></tr>
      <tr><td>載板族群</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-bull">看多</td><td class="m-na">—</td><td class="m-bull">看多</td><td class="m-own">✓</td></tr>
      <tr><td>機器人族群</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-nbull">偏多</td><td class="m-na">—</td><td class="m-nbull">偏多</td><td class="m-na">—</td></tr>
      <tr><td>SpaceX（IPO）</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-bull">看多</td><td class="m-na">計劃</td></tr>
      <tr><td>Tesla</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-neu">中立</td><td class="m-own">降低</td></tr>
      <tr><td>CrowdStrike</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-bull">看多</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td></tr>
      <tr><td>世界先進</td><td class="m-bull">看多</td><td class="m-bull">看多</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td></tr>
      <tr><td>台灣房地產</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-bear">看空</td><td class="m-na">—</td><td class="m-na">—</td></tr>
    </table>
  </div>
</div>

<div class="section">
  <div class="sec-title">🏃 孟公個人旅程（六集側記）</div>
  <div class="card">
    <div class="trend-timeline">
      <div class="trow"><span class="ep-tag">EP660</span><div class="ttext">ZZSleeper 枕頭使用心得；進入「尖末期」模式，拒絕幫朋友推薦個股。</div></div>
      <div class="trow"><span class="ep-tag">EP661</span><div class="ttext">台中旅遊帶家人去 PinoCoco 餐廳；觀察到幾乎全是節目聽眾；紅酒入坑（從最貴開始試）。</div></div>
      <div class="trow"><span class="ep-tag">EP662</span><div class="ttext">二兒子安哥出生故事：單腎、囊腫、髖關節、腸道異常，轉診台大施景中醫師，化險為夷；安哥健康快樂地跑來跑去。</div></div>
      <div class="trow"><span class="ep-tag">EP663</span><div class="ttext">🎉 78kg 達標！從 84-85kg 花一個多月達成；瘦肉針（Semaglutide）有效；健身計劃確立（網球＋重訓＋帶小孩走路）；目標繼續推進到 72-73kg。</div></div>
      <div class="trow"><span class="ep-tag">EP664</span><div class="ttext">在德國 Royal Grill 發現羅曼尼康帝 Grand Cru 僅需 80 歐元享用；紅酒指數 2020 年見頂連跌 3 年；帳戶 5 月績效超越 4 月新高。</div></div>
      <div class="trow"><span class="ep-tag">EP665</span><div class="ttext">夏天打網球差點昏倒，教練制止；🎵 諾亞（大兒子）聽出所有寶可夢音效，孟公推測是絕對音感遺傳，決定重金聘請鋼琴老師。</div></div>
    </div>
  </div>
</div>
"""

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #0f1117; color: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang TC", "Noto Sans TC", sans-serif; font-size: 15px; line-height: 1.6; }
.site-header { background: linear-gradient(135deg,#1a1f2e 0%,#16213e 100%); border-bottom: 1px solid #2d3748; padding: 24px 20px; text-align: center; }
.site-header h1 { font-size: 1.75rem; font-weight: 700; color: #90cdf4; }
.site-header p { color: #718096; margin-top: 6px; font-size: 0.88rem; }
.tab-nav { background: #1a202c; border-bottom: 1px solid #2d3748; display: flex; overflow-x: auto; padding: 0 16px; position: sticky; top: 0; z-index: 100; }
.tab-nav::-webkit-scrollbar { height: 3px; }
.tab-nav::-webkit-scrollbar-thumb { background: #4299e1; }
.tab-btn { background: none; border: none; border-bottom: 3px solid transparent; color: #718096; cursor: pointer; font-size: 0.82rem; font-weight: 700; letter-spacing: 0.04em; padding: 14px 16px; white-space: nowrap; transition: color .2s, border-color .2s; }
.tab-btn:hover { color: #90cdf4; }
.tab-btn.active { color: #90cdf4; border-bottom-color: #4299e1; }
.tab-content { display: none; }
.tab-content.active { display: block; }
.container { max-width: 960px; margin: 0 auto; padding: 28px 18px; }
.ep-header { background: linear-gradient(135deg,#1a1f2e 0%,#16213e 100%); border: 1px solid #2d3748; border-radius: 12px; padding: 22px 26px; margin-bottom: 28px; }
.ep-num { font-size: 0.75rem; font-weight: 700; color: #4299e1; text-transform: uppercase; letter-spacing: .08em; }
.ep-header h2 { font-size: 1.3rem; font-weight: 700; color: #e2e8f0; margin: 8px 0 6px; }
.meta { color: #718096; font-size: 0.83rem; }
.section { margin-bottom: 34px; }
.sec-title { color: #90cdf4; font-size: 0.95rem; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; padding-bottom: 10px; border-bottom: 1px solid #2d3748; margin-bottom: 16px; }
.summary-box { background: #1a202c; border: 1px solid #2d3748; border-radius: 12px; padding: 22px 26px; color: #a0aec0; line-height: 1.85; white-space: pre-wrap; font-size: 0.9rem; }
.card { background: #1a202c; border: 1px solid #2d3748; border-radius: 12px; padding: 18px 22px; margin-bottom: 14px; }
.card:last-child { margin-bottom: 0; }
.news-title { font-size: 0.98rem; font-weight: 700; color: #e2e8f0; margin-bottom: 8px; }
.news-meta { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }
.badge { padding: 2px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 700; letter-spacing: .03em; display: inline-block; }
.b-cat { background: #2c5282; color: #90cdf4; }
.b-ref { background: #2d3748; color: #718096; }
.b-owned { background: #553c9a; color: #d6bcfa; }
.s-bull { background: #276749; color: #9ae6b4; }
.s-watch { background: #744210; color: #fbd38d; }
.s-neu { background: #2d3748; color: #a0aec0; }
.s-bear { background: #742a2a; color: #fc8181; }
.s-nbull { background: #1a4731; color: #68d391; }
.a-buy { background: #276749; color: #9ae6b4; }
.a-sell { background: #742a2a; color: #fc8181; }
.a-hold { background: #2d3748; color: #a0aec0; }
.a-watch { background: #744210; color: #fbd38d; }
.news-event { color: #a0aec0; font-size: 0.88rem; line-height: 1.7; margin-bottom: 10px; }
.blockquote { background: #0f1117; border-left: 3px solid #4299e1; padding: 10px 14px; color: #cbd5e0; font-size: 0.86rem; line-height: 1.7; border-radius: 0 6px 6px 0; }
.blockquote-purple { background: #0f1117; border-left: 3px solid #805ad5; padding: 10px 14px; color: #cbd5e0; font-size: 0.86rem; font-style: italic; line-height: 1.7; border-radius: 0 6px 6px 0; margin: 8px 0; }
.disc-asset { font-weight: 700; color: #e2e8f0; font-size: 0.93rem; margin: 8px 0 4px; }
.disc-status { color: #718096; font-size: 0.8rem; margin-top: 6px; }
.stock-hdr { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }
.stock-name { font-size: 0.97rem; font-weight: 700; color: #e2e8f0; }
.stock-badges { display: flex; gap: 7px; flex-wrap: wrap; }
.tickers { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.ticker { background: #2a4365; color: #90cdf4; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; font-family: monospace; }
.risk-line { color: #a0aec0; font-size: 0.8rem; margin-bottom: 8px; }
.analysis-text { color: #a0aec0; font-size: 0.88rem; line-height: 1.75; }
.qa-sender { font-size: 0.75rem; font-weight: 700; color: #4299e1; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 6px; }
.qa-q { font-weight: 600; color: #e2e8f0; font-size: 0.92rem; line-height: 1.6; margin-bottom: 10px; }
.qa-pts { list-style: none; margin-bottom: 10px; }
.qa-pts li { color: #a0aec0; font-size: 0.85rem; padding: 3px 0 3px 18px; position: relative; line-height: 1.7; }
.qa-pts li::before { content: "▸"; position: absolute; left: 0; color: #4299e1; }
.trend-timeline { display: flex; flex-direction: column; gap: 10px; margin-bottom: 14px; }
.trow { display: flex; gap: 12px; align-items: flex-start; }
.ep-tag { background: #2a4365; color: #90cdf4; font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; white-space: nowrap; margin-top: 3px; font-family: monospace; }
.ttext { color: #a0aec0; font-size: 0.87rem; line-height: 1.65; }
.trend-conclusion { background: #0f1117; border-left: 3px solid #4299e1; padding: 12px 16px; color: #cbd5e0; font-size: 0.88rem; line-height: 1.7; border-radius: 0 6px 6px 0; }
.arc-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 12px; margin-bottom: 16px; }
@media (max-width:600px) { .arc-grid { grid-template-columns: repeat(2,1fr); } }
.arc-card { background: #1a202c; border: 1px solid #2d3748; border-radius: 10px; padding: 14px; text-align: center; }
.arc-ep { font-size: 0.72rem; font-weight: 700; color: #4299e1; }
.arc-mood { font-size: 0.88rem; font-weight: 700; margin: 6px 0 4px; }
.arc-date { font-size: 0.7rem; color: #4a5568; }
.arc-desc { font-size: 0.75rem; color: #718096; margin-top: 4px; }
.matrix-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
.matrix-table th { background: #1a202c; color: #718096; padding: 8px 12px; text-align: center; border: 1px solid #2d3748; font-weight: 600; white-space: nowrap; }
.matrix-table td { padding: 7px 10px; border: 1px solid #2d3748; text-align: center; }
.matrix-table td:first-child { text-align: left; font-weight: 600; color: #cbd5e0; white-space: nowrap; }
.m-bull { color: #9ae6b4; font-weight: 700; }
.m-watch { color: #fbd38d; }
.m-nbull { color: #68d391; }
.m-neu { color: #a0aec0; }
.m-bear { color: #fc8181; }
.m-na { color: #2d3748; }
.m-own { color: #d6bcfa; font-weight: 700; }
"""

JS = """
function showTab(id, btn) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  btn.classList.add('active');
}
"""

TAB_LABELS = [
    ("ep660","EP660 · 05/09"),
    ("ep661","EP661 · 05/13"),
    ("ep662","EP662 · 05/16"),
    ("ep663","EP663 · 05/20"),
    ("ep664","EP664 · 05/23"),
    ("ep665","EP665 · 05/27"),
    ("trend","📊 整體趨勢"),
]

tab_nav = ""
for i,(tid,label) in enumerate(TAB_LABELS):
    active = ' active' if i==0 else ''
    tab_nav += f'<button class="tab-btn{active}" onclick="showTab(\'{tid}\',this)">{label}</button>\n'

ep_contents = ""
for i,(eid,_) in enumerate(TAB_LABELS[:-1]):
    active = ' active' if i==0 else ''
    ep_contents += f'<div class="tab-content{active}" id="{eid}"><div class="container">{render_ep(eid)}</div></div>\n'

trend_content = f'<div class="tab-content" id="trend"><div class="container">{TREND_HTML}</div></div>'

html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>股癌 EP660–665 分析報告</title>
<style>{CSS}</style>
</head>
<body>
<header class="site-header">
  <h1>股癌 Gooaye Podcast 分析報告</h1>
  <p>EP660 – EP665 &nbsp;·&nbsp; 2026年5月 &nbsp;·&nbsp; 主持人：謝孟恭</p>
</header>
<nav class="tab-nav">{tab_nav}</nav>
{ep_contents}
{trend_content}
<script>{JS}</script>
</body>
</html>"""

out = f"{base}/gooaye_660_665_report.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Written: {out} ({len(html):,} bytes)")
