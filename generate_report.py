#!/usr/bin/env python3
import json, os, re, datetime

base = "/Users/linqian/Desktop/Gooaye podcasts"

eps = {}
for ep in ["ep660","ep661","ep662","ep663","ep664","ep665","ep666","ep667","ep668","ep669",
           "ep670","ep671","ep672","ep673","ep674","ep675","ep676","ep677","ep678"]:
    with open(f"{base}/{ep}_analysis.json", encoding="utf-8") as f:
        eps[ep] = json.load(f)

# ── helpers ──────────────────────────────────────────────
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

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

# ── stock price data ──────────────────────────────────────
TICKER_MAP = {
    # Taiwan stocks (normalize to Yahoo Finance .TW format)
    "2327.TW": "2327.TW", "2492.TW": "2492.TW", "2472.TW": "2472.TW",
    "6154.TW": "6154.TW", "2622.TW": "2622.TW", "2330.TW": "2330.TW",
    "2454.TW": "2454.TW", "5347.TW": "5347.TW", "3037.TW": "3037.TW",
    "8046.TW": "8046.TW", "2317.TW": "2317.TW", "2382.TW": "2382.TW",
    "2404.TW": "2404.TW", "2349.TW": "2349.TW", "6531.TW": "6531.TW",
    "6173.TW": "6173.TW", "2303.TW": "2303.TW",
    # US stocks
    "NVDA": "NVDA", "TSM": "TSM", "QCOM": "QCOM", "AVGO": "AVGO",
    "GOOGL": "GOOGL", "CRWD": "CRWD", "CRM": "CRM", "NOW": "NOW",
    "OKTA": "OKTA", "SNOW": "SNOW", "IGV": "IGV", "AMD": "AMD",
    "INTC": "INTC", "HPE": "HPE", "DELL": "DELL", "TSLA": "TSLA",
    "TXN": "TXN", "ON": "ON", "WDC": "WDC", "GFS": "GFS",
    "VPG": "VPG", "VSH": "VSH", "MRVL": "MRVL", "ADI": "ADI",
    # EP668-678 新增
    "2312.TW": "2312.TW", "2344.TW": "2344.TW", "2357.TW": "2357.TW",
    "2449.TW": "2449.TW", "2881.TW": "2881.TW", "3443.TW": "3443.TW",
    "6409.TW": "6409.TW", "3711.TW": "3711.TW",
    "AAPL": "AAPL", "ADBE": "ADBE", "META": "META", "MU": "MU",
    "NET": "NET", "PLTR": "PLTR", "STM": "STM", "IFNNY": "IFNNY",
    "VIAV": "VIAV", "CRWV": "CRWV", "ASTS": "ASTS",
    "RKLV": "RKLB", "RKLB": "RKLB",
}

TICKER_NAMES = {
    "2327.TW": "國巨", "2492.TW": "華新科", "2472.TW": "立隆電",
    "6154.TW": "安碁", "2622.TW": "金山電", "2330.TW": "台積電",
    "2454.TW": "聯發科", "5347.TW": "世界先進", "3037.TW": "欣興",
    "8046.TW": "南電", "2317.TW": "鴻海", "2382.TW": "廣達",
    "2404.TW": "漢唐", "2349.TW": "錸德", "6531.TW": "愛普",
    "6173.TW": "信昌電", "2303.TW": "聯電",
    "NVDA": "NVIDIA", "TSM": "台積電ADR", "QCOM": "高通",
    "AVGO": "博通", "GOOGL": "Google", "CRWD": "CrowdStrike",
    "CRM": "Salesforce", "NOW": "ServiceNow", "OKTA": "Okta",
    "SNOW": "Snowflake", "IGV": "IGV ETF", "AMD": "AMD",
    "INTC": "Intel", "HPE": "HPE", "DELL": "Dell",
    "TSLA": "Tesla", "TXN": "德儀", "ON": "安森美",
    "WDC": "Western Digital", "GFS": "GlobalFoundries",
    "VPG": "VPG", "VSH": "Vishay", "MRVL": "Marvell", "ADI": "ADI",
    "2312.TW": "金寶", "2344.TW": "華邦電", "2357.TW": "華碩",
    "2449.TW": "京元電子", "2881.TW": "富邦金", "3443.TW": "創意",
    "6409.TW": "旭隼", "3711.TW": "日月光投控",
    "AAPL": "Apple", "ADBE": "Adobe", "META": "Meta", "MU": "美光",
    "NET": "Cloudflare", "PLTR": "Palantir", "STM": "意法半導體",
    "IFNNY": "英飛凌", "VIAV": "Viavi", "CRWV": "CoreWeave",
    "ASTS": "AST SpaceMobile", "RKLB": "Rocket Lab",
}

# Collect all mentioned tickers from all episodes
def collect_tickers():
    seen = {}  # ticker -> list of episodes
    for ep_key, d in eps.items():
        ep_label = d["episode"]
        for stock in d.get("stockAnalysis", []):
            for raw_t in (stock.get("tickers") or []):
                t = raw_t.strip()
                if re.fullmatch(r"\d{4}", t):
                    t = t + ".TW"
                if t in TICKER_MAP:
                    yf_t = TICKER_MAP[t]
                    if yf_t not in seen:
                        seen[yf_t] = []
                    if ep_label not in seen[yf_t]:
                        seen[yf_t].append(ep_label)
    return seen

def fetch_stock_data():
    try:
        import yfinance as yf
    except ImportError:
        return {}

    ticker_eps = collect_tickers()
    tickers = list(ticker_eps.keys())
    if not tickers:
        return {}

    result = {}
    now = datetime.datetime.now()

    for t in tickers:
        try:
            obj = yf.Ticker(t)
            hist = obj.history(period="3mo")
            if hist.empty:
                continue

            price_now = hist["Close"].iloc[-1]
            price_1w  = hist["Close"].iloc[-6] if len(hist) >= 6 else hist["Close"].iloc[0]
            price_1m  = hist["Close"].iloc[-22] if len(hist) >= 22 else hist["Close"].iloc[0]
            price_3m  = hist["Close"].iloc[0]

            def pct(a, b):
                return round((a - b) / b * 100, 2) if b else None

            info = {}
            try:
                info = obj.info or {}
            except Exception:
                pass

            earnings_date = None
            try:
                cal = obj.calendar
                if cal is not None and not cal.empty:
                    col = "Earnings Date" if "Earnings Date" in cal.columns else cal.columns[0]
                    val = cal[col].iloc[0] if len(cal) > 0 else None
                    if val is not None:
                        if hasattr(val, "strftime"):
                            earnings_date = val.strftime("%Y-%m-%d")
                        else:
                            earnings_date = str(val)[:10]
            except Exception:
                pass

            market = "TW" if t.endswith(".TW") else "US"
            currency = "TWD" if market == "TW" else "USD"

            result[t] = {
                "name": TICKER_NAMES.get(t, t),
                "price": round(price_now, 2),
                "currency": currency,
                "chg_1w": pct(price_now, price_1w),
                "chg_1m": pct(price_now, price_1m),
                "chg_3m": pct(price_now, price_3m),
                "eps_date": earnings_date,
                "episodes": ticker_eps.get(t, []),
                "market": market,
            }
        except Exception as e:
            print(f"  警告：無法取得 {t} 資料：{e}")

    return result

print("正在抓取股價資料（需要 30-60 秒）...")
stock_data = fetch_stock_data()
print(f"完成：取得 {len(stock_data)} 支股票資料")

# ── render episode tab ────────────────────────────────────
def render_ep(ep):
    d = eps[ep]
    parts = []
    parts.append(
        f'<div class="ep-header">'
        f'<div class="ep-num">{esc(d["episode"])}</div>'
        f'<h2>{esc(d["title"])}</h2>'
        f'<div class="meta">📅 {esc(d["date"])} &nbsp;·&nbsp; ⏱ {esc(str(d.get("durationMin","?")))} 分鐘 &nbsp;·&nbsp; 👤 {esc(d.get("host","謝孟恭"))}</div>'
        f'</div>'
    )

    # Summary
    parts.append(
        '<div class="section"><div class="sec-title">📝 集數摘要</div>'
        f'<div class="summary-box">{esc(d["summary"])}</div></div>'
    )

    # News
    news_html = ""
    for n in d["news"]:
        news_html += (
            f'<div class="card">'
            f'<div class="news-title">{esc(n["title"])}</div>'
            f'<div class="news-meta"><span class="badge b-cat">{esc(n["category"])}</span>'
            f'<span class="badge b-ref">⏱ {esc(n["sourceRef"])}</span></div>'
            f'<div class="news-event">{esc(n["event"])}</div>'
            f'<div class="blockquote">{esc(n["opinion"])}</div>'
            f'</div>'
        )
    parts.append(f'<div class="section"><div class="sec-title">📰 新聞事件（{len(d["news"])} 則）</div>{news_html}</div>')

    # Host Disclosure
    disc_html = ""
    for disc in d["hostDisclosure"]:
        ac = action_class(disc["action"])
        disc_html += (
            f'<div class="card">'
            f'<span class="badge {ac}">{esc(disc["action"])}</span>'
            f'<div class="disc-asset">{esc(disc.get("asset", disc.get("stocks", "")))}</div>'
            f'<div class="blockquote-purple">「{esc(disc["quote"])}」</div>'
            f'<div class="disc-status">📌 {esc(disc.get("status", disc.get("detail", "")))}</div>'
            f'</div>'
        )
    parts.append(f'<div class="section"><div class="sec-title">⭐ 主持人持倉揭露（{len(d["hostDisclosure"])} 則）</div>{disc_html}</div>')

    # Stock Analysis
    stock_html = ""
    for s in d["stockAnalysis"]:
        sc = sentiment_class(s["sentiment"])
        sl = sentiment_label(s["sentiment"])
        tickers = "".join(f'<span class="ticker">{esc(t)}</span>' for t in (s.get("tickers") or []))
        owned = '<span class="badge b-owned">★ 持有</span>' if s.get("hostOwned") else ""
        stock_html += (
            f'<div class="card">'
            f'<div class="stock-hdr">'
            f'<div class="stock-name">{esc(s["name"])}</div>'
            f'<div class="stock-badges"><span class="badge {sc}">{sl}</span>{owned}</div>'
            f'</div>'
            f'<div class="tickers">{tickers}</div>'
            f'<div class="risk-line">⚠ 風險：{esc(str(s.get("risk", "")))}</div>'
            f'<div class="analysis-text">{esc(s["analysis"])}</div>'
            f'</div>'
        )
    parts.append(f'<div class="section"><div class="sec-title">📊 個股/族群分析（{len(d["stockAnalysis"])} 則）</div>{stock_html}</div>')

    # QA
    qa_html = ""
    for q in d["qa"]:
        pts = "".join(f'<li>{esc(p)}</li>' for p in q["answerPoints"])
        sender = q.get("sender") or q.get("questioner", "")
        qa_html += (
            f'<div class="card">'
            f'<div class="qa-sender">@ {esc(sender)}</div>'
            f'<div class="qa-q">{esc(q["question"])}</div>'
            f'<ul class="qa-pts">{pts}</ul>'
            f'<div class="blockquote">{esc(q["keyTakeaway"])}</div>'
            f'</div>'
        )
    parts.append(f'<div class="section"><div class="sec-title">💬 聽眾問答（{len(d["qa"])} 則）</div>{qa_html}</div>')

    return "\n".join(parts)

# ── render stock price tab ────────────────────────────────
def pct_class(v):
    if v is None: return "pct-na"
    if v > 3: return "pct-up2"
    if v > 0: return "pct-up1"
    if v < -3: return "pct-dn2"
    if v < 0: return "pct-dn1"
    return "pct-flat"

def pct_fmt(v):
    if v is None: return "—"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.2f}%"

def render_stock_tab():
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    if not stock_data:
        return '<div class="container"><div class="card" style="color:#a0aec0;">無法取得股價資料，請確認網路連線。</div></div>'

    tw_stocks = {k: v for k, v in stock_data.items() if v["market"] == "TW"}
    us_stocks = {k: v for k, v in stock_data.items() if v["market"] == "US"}

    def table_section(title, stocks_dict):
        if not stocks_dict:
            return ""
        rows = ""
        for ticker, d in sorted(stocks_dict.items()):
            ep_badges = "".join(f'<span class="ep-badge">{esc(e)}</span>' for e in d["episodes"])
            eps_cell = f'<td class="eps-cell">{esc(d.get("eps_date") or "—")}</td>'
            rows += (
                f'<tr>'
                f'<td class="tk-cell"><span class="ticker">{esc(ticker)}</span></td>'
                f'<td class="name-cell">{esc(d["name"])}</td>'
                f'<td class="price-cell">{esc(str(d["price"]))} <span class="currency">{esc(d["currency"])}</span></td>'
                f'<td class="{pct_class(d["chg_1w"])}">{pct_fmt(d["chg_1w"])}</td>'
                f'<td class="{pct_class(d["chg_1m"])}">{pct_fmt(d["chg_1m"])}</td>'
                f'<td class="{pct_class(d["chg_3m"])}">{pct_fmt(d["chg_3m"])}</td>'
                f'{eps_cell}'
                f'<td class="ep-mentions">{ep_badges}</td>'
                f'</tr>'
            )
        return f'''
<div class="section">
  <div class="sec-title">{title}</div>
  <div class="card" style="overflow-x:auto;padding:0;">
    <table class="price-table">
      <thead><tr>
        <th>代碼</th><th>名稱</th><th>現價</th>
        <th>1週</th><th>1月</th><th>3月</th>
        <th>下次財報</th><th>出現集數</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>'''

    tw_section = table_section("🇹🇼 台股", tw_stocks)
    us_section = table_section("🇺🇸 美股", us_stocks)

    disclaimer = f'''
<div class="section">
  <div class="card" style="color:#718096;font-size:0.78rem;line-height:1.7;">
    ⚠ 股價資料由 Yahoo Finance 提供，僅供參考，非即時資料（有延遲）。財報日期可能更新，請以官方公告為準。
    本頁資料更新時間：{now_str}
  </div>
</div>'''

    return f'<div class="container">{tw_section}{us_section}{disclaimer}</div>'

# ── trend HTML ────────────────────────────────────────────
TREND_HTML = """
<div class="section">
  <div class="sec-title">🔥 缺料漲價主軸：被動元件 → 功率元件 → 封測/導線架（EP660–EP678）</div>
  <div class="card">
    <div class="trend-timeline">
      <div class="trow"><span class="ep-tag">EP660</span><div class="ttext">全球被動元件同步噴發（日/美/台）；MLCC 排擠效應出現；AI 高規格 47μF 嚴重缺貨；孟公確認「不應該低估這個題材」。</div></div>
      <div class="trow"><span class="ep-tag">EP661</span><div class="ttext">台灣被動元件正式追上國際；鋁電容深度剖析（立隆電、金山電、裕邦 vs 日本 Nichicon/NipponChemical）；Power 廠直接包產能是先行確認信號。</div></div>
      <div class="trow"><span class="ep-tag">EP662</span><div class="ttext">Panasonic SPCAP 確認漲價 30%（六月初生效）；Rohm 漲價信即將落地；電阻同期也漲 30%；採購開始在現貨市場掃貨。</div></div>
      <div class="trow"><span class="ep-tag">EP663</span><div class="ttext">漲價信正式落地（選擇性對部分客戶）；蜜旺時通路商公開確認斷供；2018 超周期類比（國巨毛利 60%+）提出；廠商保守擴產是多頭持久的關鍵。</div></div>
      <div class="trow"><span class="ep-tag">EP664</span><div class="ttext">全線漲停：MLCC、鋁電容、電感、電阻、通路商齊噴；中國江海股份飆漲；日本 Chemical 廠單日漲超 10%；NVIDIA 產能包場光通訊雷射策略確認。</div></div>
      <div class="trow"><span class="ep-tag">EP665</span><div class="ttext">國巨法說確認：特規品稼動率 90%、標準品 80%+、BBR Ratio 持續提升；孟公形容「整組做壞掉，射個滿臉完全看不懂」；每次假摔後又繼續噴出去。</div></div>
      <div class="trow"><span class="ep-tag">EP666</span><div class="ttext">鋁電容 20%+ 全球缺貨（江海備忘錄）；被動元件從「cost-driven」轉向「demand-driven」敘事；老 AI 全面復活（富士康/廣達漲停）；軟體股全面爆發（IGVETF 新高）。</div></div>
      <div class="trow"><span class="ep-tag">EP667</span><div class="ttext">被動元件族群開始橫盤整理，主持人認為是健康訊號；持倉均未破 14 日線；等待月線作為最終底線；TSMC 形態轉強、大型股補漲行情浮現。</div></div>
      <div class="trow"><span class="ep-tag">EP670</span><div class="ttext">被動元件漲價全面確認：國巨目標價 237；電阻原估 6-7 輪漲價、現在只要 2 輪就達終值——漲價速度遠超原先預期。</div></div>
      <div class="trow"><span class="ep-tag">EP671</span><div class="ttext">🔑 功率元件新機會首次登場：Nexperia 制裁事件觸發供應鏈重組，被動元件的劇本準備在功率元件重演一次。</div></div>
      <div class="trow"><span class="ep-tag">EP672</span><div class="ttext">全球一線 IDM（Infineon/ON/STM/Rohm）AI 訂單強勁，Lead Time 拉到 9 週以上；採購開始驗證台廠——與當年日系鋁電容缺貨、台系受益的模式如出一轍。</div></div>
      <div class="trow"><span class="ep-tag">EP673</span><div class="ttext">盤面拉回別驚慌；電阻確認是被動元件下一棒；國巨在修正中展現超強韌性。</div></div>
      <div class="trow"><span class="ep-tag">EP675</span><div class="ttext">被動元件已到「射到宇宙」等級，7 月密集漲價通知將至；MOSFET 開始出現缺貨回報（ODM/EMS 端）；IC 設計轉強。</div></div>
      <div class="trow"><span class="ep-tag">EP676</span><div class="ttext">MOSFET 全面確認缺貨（ODM/EMS 買不到、零庫存）；🔑 封測成為新主題：報價季增 30-40%（COVID 時僅 10-20%），AI 排擠效應發威。</div></div>
      <div class="trow"><span class="ep-tag">EP677</span><div class="ttext">功率元件站上 5 日/10 日線最強勢；被動元件整理但守住季線；CCL/矽晶圓依然強勢；IC 設計全面轉強。</div></div>
      <div class="trow"><span class="ep-tag">EP678</span><div class="ttext">ADI 發出漲價訊號＝功率元件全面漲價確認；🔑 導線架交期 3-4 個月拉到 7-8 個月、漲 10-20%，成為新的供應鏈瓶頸；封測廠獲利大幅跳升（漲價＋稼動率拉滿）。</div></div>
    </div>
    <div class="trend-conclusion">結論：缺料漲價主軸持續擴散升級——被動元件（EP660-670 漲價確認）→ 功率元件（EP671 登場、EP678 ADI 訊號全面確認）→ 封測（EP676 登場、30-40% 漲價）→ 導線架（EP678 新瓶頸）。孟公被動元件＋功率元件全程持有，「成本低就抱著」，每一棒都在前一棒確認後提前佈局下一棒。</div>
  </div>
</div>

<div class="section">
  <div class="sec-title">🔄 老 AI 族群 ＋ Computex 2026 資金輪動弧線</div>
  <div class="card">
    <div class="trend-timeline">
      <div class="trow"><span class="ep-tag">EP660</span><div class="ttext">成熟製程/消費 IC 族群輪動觀察：世界先進、GlobalFoundries、環球晶、瑞昱、聯詠走強，補庫存假說提出。</div></div>
      <div class="trow"><span class="ep-tag">EP661</span><div class="ttext">投信增持台積電上限放寬確認，需 2-3 個月修公開說明書；中小股籌碼面承壓預警；孟公調整為高低配（台積電＋聯發科 核心 ＋ 被動元件）。</div></div>
      <div class="trow"><span class="ep-tag">EP662</span><div class="ttext">禮拜五大跌，老 AI 摔最重，主因毛利率短期承壓；孟公不減碼反而在跌停板買進；「太弱留強」心法：回檔後最快站回的就是下一波主流。</div></div>
      <div class="trow"><span class="ep-tag">EP663</span><div class="ttext">APMemory 復活案例說明老 AI 故事未結束；資金輪動中的被動元件族群強勢；孟公多個標的進入處置股，盤中無法操作。</div></div>
      <div class="trow"><span class="ep-tag">EP664</span><div class="ttext">老 AI 多頭確立，Anthropic 轉獲利打臉泡沫論，Google TPU Cluster 外銷比 3:1 超預期；資金面持續確認 AI 硬體投資不縮減。</div></div>
      <div class="trow"><span class="ep-tag">EP665</span><div class="ttext">機器人族群與載板繼續強勢；SpaceX IPO 成為下一個資金目標；衛星相關已出脫（賺到魚頭），計劃買進 SpaceX 並降低 Tesla。</div></div>
      <div class="trow"><span class="ep-tag">EP666</span><div class="ttext">老 AI 全面復活（鴻海/廣達漲停，陳泰銘成首富）；軟體股全爆（IGVETF 新高，Salesforce 回購，Okta/Snowflake 超預期）；AI 末日論自打臉（Dario/Sam 轉向）。</div></div>
      <div class="trow"><span class="ep-tag">EP667</span><div class="ttext">Computex 2026：黃仁勳點名 Marvell 兆元企業→MRVL 噴出；NVIDIA DJX Spark AIPC 第二波；光通訊再成共識；TSMC/NVIDIA 大型股補漲行情浮現。</div></div>
      <div class="trow"><span class="ep-tag">EP668</span><div class="ttext">主持人親身參觀 Computex 2026，近兩三年最喜歡的一屆；一般民眾進展會、追星黃仁勳被視為「全民參與市場」的正面訊號。</div></div>
      <div class="trow"><span class="ep-tag">EP670</span><div class="ttext">SpaceX 正式上市，主持人 IPO 申購成功＋二級市場約 160 美元加碼；衛星概念股（RKLB/ASTS 等）全數出清——「本尊上市，替代品退場」。</div></div>
      <div class="trow"><span class="ep-tag">EP672</span><div class="ttext">台股歷史新高確認，驗證上集「修正結束」預判；提醒確認偏誤：別用自己的持股漲跌判斷大盤方向。</div></div>
      <div class="trow"><span class="ep-tag">EP674</span><div class="ttext">2026 上半年總結：績效歷史新高。路徑：Q1 衛星→窄版→玻璃基板；Q2 被動元件為主軸；蘋果漲價事件。</div></div>
      <div class="trow"><span class="ep-tag">EP675</span><div class="ttext">6/30 收官日；再平衡賣壓結束；自我檢討：修正期間換倉過多，「動作太多」是上半年最大的操作缺點。</div></div>
      <div class="trow"><span class="ep-tag">EP677</span><div class="ttext">新世代槓桿文化衝擊：信用＋質押＋股期＋滾 = 5-6 倍槓桿 vs 主持人上限 2.5 倍；韓式槓桿去化造成台股中小型股股期跌停、現貨僅跌 3-5% 的異常波動。</div></div>
      <div class="trow"><span class="ep-tag">EP678</span><div class="ttext">颱風假閉市但「散漲」：富台 +3%；NVIDIA 重回 210 站上季線；Meta 確認 doubledown AI；光通內部輪動：NarrowFast（矽光/GaAs）被賣、WideandSlow（VCSEL）被買。</div></div>
    </div>
    <div class="trend-conclusion">結論：EP660-667 是被動元件行情的主升段；EP668-674 資金轉向 SpaceX 上市與功率元件，台股創高後上半年以歷史新高績效收官；EP675-678 進入槓桿去化的震盪期，主持人質押被鎖反而「被迫冷靜」，功率元件/封測接棒成為最強主線，等待 TSMC 法說與大盤新高開啟下一波。</div>
  </div>
</div>

<div class="section">
  <div class="sec-title">🚀 主題追蹤：SpaceX / 光通訊 / 功率元件 / 機器人 / Edge AI</div>
  <div class="card">
    <div class="trend-timeline">
      <div class="trow"><span class="ep-tag">SpaceX</span><div class="ttext">EP665 首次登場（Starlink 印鈔機＋軌道 AI DataCenter）→ EP670 正式上市，主持人 IPO 申購＋二級市場 160 美元加碼，衛星概念股全數出清 → EP677 「巴菲特一生財富 = SpaceX 一天的波動」。長期核心持倉。</div></div>
      <div class="trow"><span class="ep-tag">功率元件</span><div class="ttext">EP667 潛力題材 → EP671 正式登場（Nexperia 制裁）→ EP672 IDM Lead Time 9週+ → EP675-676 MOSFET 缺貨確認 → EP678 ADI 漲價訊號＝全面漲價。已成為最強主線，主持人持有。</div></div>
      <div class="trow"><span class="ep-tag">封測/導線架</span><div class="ttext">EP676 封測登場（30-40% 漲價、AI 排擠效應、IDM 自有封測廠最優）→ EP678 導線架交期 7-8 個月成新瓶頸，「有封裝產能但沒導線架」的斷鏈風險浮現。</div></div>
      <div class="trow"><span class="ep-tag">光通訊</span><div class="ttext">EP664 NVIDIA 包場確認 → EP667 Computex 共識 → EP676 依然「沒有資金」 → EP678 內部輪動：NarrowFast（矽光/GaAs 雷射）被賣、WideandSlow（VCSEL）被買，銅相關（先前被誤殺）創新高。主持人未配置，等大盤新高。</div></div>
      <div class="trow"><span class="ep-tag">機器人</span><div class="ttext">EP672 主持人透露已佈局日系減速機股票，視為機器人題材的早期切入點：從確定受益的核心零組件切入，而非押注整機廠。</div></div>
      <div class="trow"><span class="ep-tag">Edge AI</span><div class="ttext">EP670 提出框架：前沿模型能力約一年後下放到端側，Edge AI 是 AI 行情的下一個一年期主題；聯發科 Triggerfish（EP673）是具體事件。</div></div>
    </div>
    <div class="trend-conclusion">截至 EP678：功率元件＋封測是當前最強主線（基本面與股價同步確認）；SpaceX 是長期信仰持倉；光通訊在等待大盤新高的資金行情；機器人與 Edge AI 是提前佈局的下一年度主題。</div>
  </div>
</div>

<div class="section">
  <div class="sec-title">📈 市場情緒弧線（EP660–EP678）</div>
  <div class="arc-grid">
    <div class="arc-card"><div class="arc-ep">EP660</div><div class="arc-mood" style="color:#fbd38d;">謹慎/尖末期</div><div class="arc-date">2026-05-09</div><div class="arc-desc">進入尖末期模式，拒絕朋友問股</div></div>
    <div class="arc-card"><div class="arc-ep">EP661</div><div class="arc-mood" style="color:#9ae6b4;">高低配樂觀</div><div class="arc-date">2026-05-13</div><div class="arc-desc">台中旅遊，紅酒入坑，策略清晰</div></div>
    <div class="arc-card"><div class="arc-ep">EP662</div><div class="arc-mood" style="color:#fbd38d;">逢跌加碼</div><div class="arc-date">2026-05-16</div><div class="arc-desc">安哥故事，禮拜五跌停買進</div></div>
    <div class="arc-card"><div class="arc-ep">EP663</div><div class="arc-mood" style="color:#9ae6b4;">強勢/達標</div><div class="arc-date">2026-05-20</div><div class="arc-desc">78kg 達標！處置股滿倉，漲停鎖住</div></div>
    <div class="arc-card"><div class="arc-ep">EP664</div><div class="arc-mood" style="color:#9ae6b4;">5月新高</div><div class="arc-date">2026-05-23</div><div class="arc-desc">全線漲停，績效超越4月，羅曼尼康帝</div></div>
    <div class="arc-card"><div class="arc-ep">EP665</div><div class="arc-mood" style="color:#90cdf4;">整組做壞掉</div><div class="arc-date">2026-05-27</div><div class="arc-desc">諾亞絕對音感，SpaceX 新主題登場</div></div>
    <div class="arc-card"><div class="arc-ep">EP666</div><div class="arc-mood" style="color:#9ae6b4;">老AI全面復活</div><div class="arc-date">2026-05-30</div><div class="arc-desc">軟體股爆發，90%持倉處置股</div></div>
    <div class="arc-card"><div class="arc-ep">EP667</div><div class="arc-mood" style="color:#fbd38d;">整理/守成</div><div class="arc-date">2026-06-03</div><div class="arc-desc">Computex，被動元件整理，大型股補漲</div></div>
    <div class="arc-card"><div class="arc-ep">EP668</div><div class="arc-mood" style="color:#9ae6b4;">樂觀/參展</div><div class="arc-date">2026-06-06</div><div class="arc-desc">Computex 親身參觀，近三年最愛的一屆</div></div>
    <div class="arc-card"><div class="arc-ep">EP669</div><div class="arc-mood" style="color:#9ae6b4;">感恩/34歲</div><div class="arc-date">2026-06-10</div><div class="arc-desc">生日，驗血紅字全消，身體素質提升</div></div>
    <div class="arc-card"><div class="arc-ep">EP670</div><div class="arc-mood" style="color:#90cdf4;">收割/轉進</div><div class="arc-date">2026-06-13</div><div class="arc-desc">SpaceX 上市買進，衛星股全數出清</div></div>
    <div class="arc-card"><div class="arc-ep">EP671</div><div class="arc-mood" style="color:#fbd38d;">尋找下一棒</div><div class="arc-date">2026-06-17</div><div class="arc-desc">功率元件登場，冒名詐騙警告</div></div>
    <div class="arc-card"><div class="arc-ep">EP672</div><div class="arc-mood" style="color:#9ae6b4;">新高確認</div><div class="arc-date">2026-06-20</div><div class="arc-desc">台股歷史新高，IDM 深度解析</div></div>
    <div class="arc-card"><div class="arc-ep">EP673</div><div class="arc-mood" style="color:#fbd38d;">拉回不驚慌</div><div class="arc-date">2026-06-24</div><div class="arc-desc">電阻下一棒，聯發科 Triggerfish</div></div>
    <div class="arc-card"><div class="arc-ep">EP674</div><div class="arc-mood" style="color:#9ae6b4;">人生高光</div><div class="arc-date">2026-06-27</div><div class="arc-desc">上半年績效歷史新高，蘋果漲價</div></div>
    <div class="arc-card"><div class="arc-ep">EP675</div><div class="arc-mood" style="color:#fbd38d;">自我檢討</div><div class="arc-date">2026-07-01</div><div class="arc-desc">收官日，換倉過多反省，MOSFET 缺貨</div></div>
    <div class="arc-card"><div class="arc-ep">EP676</div><div class="arc-mood" style="color:#9ae6b4;">新主題發酵</div><div class="arc-date">2026-07-04</div><div class="arc-desc">封測 30-40% 漲價，Meta doubledown</div></div>
    <div class="arc-card"><div class="arc-ep">EP677</div><div class="arc-mood" style="color:#90cdf4;">被迫冷靜</div><div class="arc-date">2026-07-08</div><div class="arc-desc">槓桿去化震盪，質押被鎖反而平靜</div></div>
    <div class="arc-card"><div class="arc-ep">EP678</div><div class="arc-mood" style="color:#9ae6b4;">蓄勢待發</div><div class="arc-date">2026-07-11</div><div class="arc-desc">颱風假散漲，NVIDIA 重回 210，導線架瓶頸</div></div>
  </div>
</div>

<div class="section">
  <div class="sec-title">📊 主題/標的情緒矩陣（按時期，EP660–EP678）</div>
  <div class="card" style="overflow-x:auto;">
    <table class="matrix-table">
      <tr><th>標的/族群</th><th>5月上<br>(660-662)</th><th>5月下<br>(663-666)</th><th>6月上<br>(667-670)</th><th>6月下<br>(671-674)</th><th>7月上<br>(675-678)</th><th>孟公持有</th></tr>
      <tr><td>被動元件族群</td><td class="m-bull">看多</td><td class="m-bull">全線噴發</td><td class="m-bull">漲價確認</td><td class="m-bull">電阻接棒</td><td class="m-bull">射到宇宙</td><td class="m-own">✓</td></tr>
      <tr><td>功率元件/IDM</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-watch">潛力</td><td class="m-bull">登場/缺貨</td><td class="m-bull">全面漲價</td><td class="m-own">✓</td></tr>
      <tr><td>封測/導線架</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-bull">30-40%漲價</td><td class="m-na">—</td></tr>
      <tr><td>SpaceX</td><td class="m-na">—</td><td class="m-bull">登場</td><td class="m-bull">上市買進</td><td class="m-bull">持有</td><td class="m-bull">持有</td><td class="m-own">✓</td></tr>
      <tr><td>衛星概念股</td><td class="m-na">—</td><td class="m-watch">魚頭出場</td><td class="m-neu">全數出清</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">已出清</td></tr>
      <tr><td>NVIDIA</td><td class="m-bull">看多</td><td class="m-watch">觀望</td><td class="m-bull">補漲</td><td class="m-na">—</td><td class="m-bull">重回210</td><td class="m-own">✓</td></tr>
      <tr><td>台積電</td><td class="m-bull">看多</td><td class="m-bull">看多</td><td class="m-bull">看多</td><td class="m-bull">看多</td><td class="m-watch">法說前</td><td class="m-na">—</td></tr>
      <tr><td>光通訊族群</td><td class="m-na">—</td><td class="m-bull">NVIDIA包場</td><td class="m-bull">共識</td><td class="m-na">—</td><td class="m-watch">內部輪動</td><td class="m-na">未配置</td></tr>
      <tr><td>記憶體</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-bull">看多</td><td class="m-bull">看多</td><td class="m-watch">已出場</td><td class="m-na">已出場</td></tr>
      <tr><td>機器人/減速機</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-bull">日系佈局</td><td class="m-na">—</td><td class="m-own">✓</td></tr>
      <tr><td>IC設計</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-watch">Triggerfish</td><td class="m-bull">全面轉強</td><td class="m-na">—</td></tr>
      <tr><td>Meta</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-bull">doubledown</td><td class="m-na">—</td></tr>
      <tr><td>Tesla</td><td class="m-na">—</td><td class="m-neu">中立</td><td class="m-na">—</td><td class="m-na">—</td><td class="m-neu">信仰持股</td><td class="m-own">✓</td></tr>
    </table>
  </div>
</div>

<div class="section">
  <div class="sec-title">🏃 孟公個人旅程（EP660–EP678 側記）</div>
  <div class="card">
    <div class="trend-timeline">
      <div class="trow"><span class="ep-tag">EP660</span><div class="ttext">ZZSleeper 枕頭使用心得；進入「尖末期」模式，拒絕幫朋友推薦個股。</div></div>
      <div class="trow"><span class="ep-tag">EP661</span><div class="ttext">台中旅遊帶家人去 PinoCoco 餐廳；觀察到幾乎全是節目聽眾；紅酒入坑（從最貴開始試）。</div></div>
      <div class="trow"><span class="ep-tag">EP662</span><div class="ttext">二兒子安哥出生故事：單腎、囊腫、髖關節、腸道異常，轉診台大施景中醫師，化險為夷；安哥健康快樂地跑來跑去。</div></div>
      <div class="trow"><span class="ep-tag">EP663</span><div class="ttext">🎉 78kg 達標！從 84-85kg 花一個多月達成；瘦肉針（Semaglutide）有效；健身計劃確立（網球＋重訓＋帶小孩走路）；目標繼續推進到 72-73kg。</div></div>
      <div class="trow"><span class="ep-tag">EP664</span><div class="ttext">在德國 Royal Grill 發現羅曼尼康帝 Grand Cru 僅需 80 歐元享用；紅酒指數 2020 年見頂連跌 3 年；帳戶 5 月績效超越 4 月新高。</div></div>
      <div class="trow"><span class="ep-tag">EP665</span><div class="ttext">夏天打網球差點昏倒，教練制止；🎵 諾亞（大兒子）聽出所有寶可夢音效，孟公推測是絕對音感遺傳，決定重金聘請鋼琴老師。</div></div>
      <div class="trow"><span class="ep-tag">EP666</span><div class="ttext">植村秀品牌贊助；持續「慢下來」哲學（內觀、坐姿調整改善下背痛）；90% 持倉在處置股中。</div></div>
      <div class="trow"><span class="ep-tag">EP667</span><div class="ttext">持續「慢下來運動」（深呼吸訓練、日常動作刻意放慢）；自費參加佳佩樂飯店品酒會，學習味覺語言，見識大哥當場開百萬特級元酒；被邀為「50碗」美食評鑑列名單。</div></div>
      <div class="trow"><span class="ep-tag">EP668</span><div class="ttext">親身參觀 Computex 2026，近兩三年最喜歡的一屆；對「死老百姓進展會、追星黃仁勳」的批評持正面看法。</div></div>
      <div class="trow"><span class="ep-tag">EP669</span><div class="ttext">🎂 34 歲生日：驗血報告紅字全消、身體素質持續提升；收到金色皮卡丘雕像、網球拍等禮物。</div></div>
      <div class="trow"><span class="ep-tag">EP670</span><div class="ttext">瘦肉素多支注射筆殘量混打＋最粗針頭的虛驚一場；體悟「任何工具都應該先讀說明書」。</div></div>
      <div class="trow"><span class="ep-tag">EP671</span><div class="ttext">警告網路有人冒充他推薦股票；林口店面觀察：房產成交量跌但屋主不降價；規劃引進餐飲業者。</div></div>
      <div class="trow"><span class="ep-tag">EP672</span><div class="ttext">岳母來台探訪；林口小生意持續篩選合夥人；二十樓陽台出現一隻蟬，視為吉兆。</div></div>
      <div class="trow"><span class="ep-tag">EP673</span><div class="ttext">全聯紅酒探索：阿根廷 Malbec、法國 Syrah、西班牙 Tempranillo、Bourgogne Chardonnay、紐西蘭 Sauvignon Blanc；口味偏好勃根地。</div></div>
      <div class="trow"><span class="ep-tag">EP674</span><div class="ttext">上半年總結：「人生的高光時刻」——減重針有效無副作用、體能提升、孩子健康問題陸續排除、績效歷史新高。</div></div>
      <div class="trow"><span class="ep-tag">EP675</span><div class="ttext">笑男資本股東會；自家貝果遊戲 RedEye Ruby 預計 7 月下旬上 Steam。</div></div>
      <div class="trow"><span class="ep-tag">EP676</span><div class="ttext">宜蘭凱渡飯店親子行（意外的好體驗，KidsClub＋江振誠 Fine Dining）；育兒感悟「一天太長，一年太短」。</div></div>
      <div class="trow"><span class="ep-tag">EP677</span><div class="ttext">觀察新世代「四代同堂」槓桿文化（5-6 倍）大受衝擊；自己質押 4 月起被鎖無法加碼，反而意外平靜。</div></div>
      <div class="trow"><span class="ep-tag">EP678</span><div class="ttext">💪 血壓從 140/89 降到約 110/70、心跳變慢，運動效果遠超預期；颱風假心境轉變：從討厭放假到覺得「多開盤未必是好事」。</div></div>
    </div>
  </div>
</div>
"""

# ── CSS ───────────────────────────────────────────────────
CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #0f1117; color: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang TC", "Noto Sans TC", sans-serif; font-size: 15px; line-height: 1.6; }
.site-header { background: linear-gradient(135deg,#1a1f2e 0%,#16213e 100%); border-bottom: 1px solid #2d3748; padding: 24px 20px; text-align: center; }
.site-header h1 { font-size: 1.75rem; font-weight: 700; color: #90cdf4; }
.site-header p { color: #718096; margin-top: 6px; font-size: 0.88rem; }
.layout { display: flex; align-items: flex-start; }
.tab-nav { background: #1a202c; border-right: 1px solid #2d3748; display: flex; flex-direction: column; width: 185px; flex-shrink: 0; position: sticky; top: 0; height: 100vh; overflow-y: auto; padding: 12px 0; z-index: 100; }
.tab-nav::-webkit-scrollbar { width: 3px; }
.tab-nav::-webkit-scrollbar-thumb { background: #4299e1; }
.tab-btn { background: none; border: none; border-left: 3px solid transparent; color: #718096; cursor: pointer; font-size: 0.82rem; font-weight: 700; letter-spacing: 0.04em; padding: 11px 18px; text-align: left; white-space: nowrap; transition: color .2s, border-color .2s, background .2s; }
.tab-btn:hover { color: #90cdf4; }
.tab-btn.active { color: #90cdf4; border-left-color: #4299e1; background: #212a3a; }
.main-area { flex: 1; min-width: 0; }
@media (max-width: 900px) {
  .layout { display: block; }
  .tab-nav { flex-direction: row; width: 100%; height: auto; overflow-x: auto; overflow-y: hidden; border-right: none; border-bottom: 1px solid #2d3748; padding: 0 12px; }
  .tab-nav::-webkit-scrollbar { height: 3px; width: auto; }
  .tab-btn { border-left: none; border-bottom: 3px solid transparent; padding: 13px 14px; }
  .tab-btn.active { border-left-color: transparent; border-bottom-color: #4299e1; background: none; }
}
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
.arc-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin-bottom: 16px; }
@media (max-width:700px) { .arc-grid { grid-template-columns: repeat(2,1fr); } }
.arc-card { background: #1a202c; border: 1px solid #2d3748; border-radius: 10px; padding: 14px; text-align: center; }
.arc-ep { font-size: 0.72rem; font-weight: 700; color: #4299e1; }
.arc-mood { font-size: 0.82rem; font-weight: 700; margin: 6px 0 4px; }
.arc-date { font-size: 0.7rem; color: #4a5568; }
.arc-desc { font-size: 0.72rem; color: #718096; margin-top: 4px; }
.matrix-table { width: 100%; border-collapse: collapse; font-size: 0.78rem; }
.matrix-table th { background: #1a202c; color: #718096; padding: 8px 10px; text-align: center; border: 1px solid #2d3748; font-weight: 600; white-space: nowrap; }
.matrix-table td { padding: 7px 8px; border: 1px solid #2d3748; text-align: center; }
.matrix-table td:first-child { text-align: left; font-weight: 600; color: #cbd5e0; white-space: nowrap; }
.m-bull { color: #9ae6b4; font-weight: 700; }
.m-watch { color: #fbd38d; }
.m-nbull { color: #68d391; }
.m-neu { color: #a0aec0; }
.m-bear { color: #fc8181; }
.m-na { color: #2d3748; }
.m-own { color: #d6bcfa; font-weight: 700; }
/* Stock price table */
.price-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; min-width: 680px; }
.price-table th { background: #16213e; color: #718096; padding: 10px 12px; text-align: center; border-bottom: 2px solid #2d3748; font-weight: 700; white-space: nowrap; }
.price-table td { padding: 9px 12px; border-bottom: 1px solid #1e2d3d; text-align: center; vertical-align: middle; }
.price-table tr:hover td { background: #1e2a3d; }
.tk-cell { text-align: left !important; }
.name-cell { text-align: left !important; color: #cbd5e0; }
.price-cell { font-weight: 700; color: #e2e8f0; white-space: nowrap; }
.currency { font-size: 0.68rem; color: #4a5568; margin-left: 2px; }
.eps-cell { font-size: 0.78rem; color: #9ae6b4; }
.ep-mentions { text-align: left !important; }
.ep-badge { display: inline-block; background: #2a4365; color: #90cdf4; font-size: 0.64rem; font-weight: 700; padding: 1px 6px; border-radius: 3px; margin: 1px 2px; font-family: monospace; }
.pct-up2 { color: #9ae6b4; font-weight: 700; }
.pct-up1 { color: #68d391; }
.pct-flat { color: #a0aec0; }
.pct-dn1 { color: #fc8181; }
.pct-dn2 { color: #fc8181; font-weight: 700; }
.pct-na  { color: #4a5568; }
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
    ("ep666","EP666 · 05/30"),
    ("ep667","EP667 · 06/03"),
    ("ep668","EP668 · 06/06"),
    ("ep669","EP669 · 06/10"),
    ("ep670","EP670 · 06/13"),
    ("ep671","EP671 · 06/17"),
    ("ep672","EP672 · 06/20"),
    ("ep673","EP673 · 06/24"),
    ("ep674","EP674 · 06/27"),
    ("ep675","EP675 · 07/01"),
    ("ep676","EP676 · 07/04"),
    ("ep677","EP677 · 07/08"),
    ("ep678","EP678 · 07/11"),
    ("trend","📊 整體趨勢"),
    ("stocks","📈 股價追蹤"),
]

tab_nav = ""
for i,(tid,label) in enumerate(TAB_LABELS):
    active = ' active' if i==0 else ''
    tab_nav += f'<button class="tab-btn{active}" onclick="showTab(\'{tid}\',this)">{label}</button>\n'

ep_contents = ""
ep_tab_ids = [t for t,_ in TAB_LABELS if t.startswith("ep")]
for i, eid in enumerate(ep_tab_ids):
    active = ' active' if i==0 else ''
    ep_contents += f'<div class="tab-content{active}" id="{eid}"><div class="container">{render_ep(eid)}</div></div>\n'

trend_content = f'<div class="tab-content" id="trend"><div class="container">{TREND_HTML}</div></div>'
stocks_content = f'<div class="tab-content" id="stocks">{render_stock_tab()}</div>'

html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>股癌 EP660–EP678 分析報告</title>
<style>{CSS}</style>
</head>
<body>
<header class="site-header">
  <h1>股癌 Gooaye Podcast 分析報告</h1>
  <p>EP660 – EP678 &nbsp;·&nbsp; 2026年5-7月 &nbsp;·&nbsp; 主持人：謝孟恭</p>
</header>
<div class="layout">
<nav class="tab-nav">{tab_nav}</nav>
<main class="main-area">
{ep_contents}
{trend_content}
{stocks_content}
</main>
</div>
<script>{JS}</script>
</body>
</html>"""

out = f"{base}/gooaye_660_665_report.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Written: {out} ({len(html):,} bytes)")

# Auto push to GitHub
import subprocess
os.chdir(base)
ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
subprocess.run(["git", "add", "-A"], check=True)
result = subprocess.run(["git", "diff", "--cached", "--quiet"])
if result.returncode != 0:
    subprocess.run(["git", "commit", "-m", f"update: EP667 + 股價追蹤功能 {ts}"], check=True)
    subprocess.run(["git", "push"], check=True)
    print(f"✓ 已推送至 GitHub ({ts})")
else:
    print("(無變更，略過推送)")
