#!/usr/bin/env python3
"""
自動分析股癌 Podcast 新集數並更新報告
可在本機或 GitHub Actions 環境執行
"""
import os, re, json, time, sys, subprocess
import urllib.request
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.abspath(__file__))
ASSEMBLYAI_KEY = os.environ.get('ASSEMBLYAI_API_KEY', '2688a0080797403b810a89ca889d7c0a')
ANTHROPIC_KEY  = os.environ.get('ANTHROPIC_API_KEY', '')
RSS_URL = 'https://feeds.soundon.fm/podcasts/954689a5-3096-43a4-a80b-7810b219cef3.xml'

PROMPT_TEMPLATE = """你是專業台股/美股投資分析師。請仔細閱讀以下股癌（Gooaye）Podcast EP{ep_num} 的完整逐字稿，從頭到尾每一分鐘都仔細聆聽，完整提取所有投資主題、個股、新聞事件與 Q&A 心法。

【最重要原則】
1. 只提取 Podcast 中明確說出的內容，不要推測、補充或編造
2. ★整集內容必須完整收錄，不可遺漏任何段落★

請輸出嚴格 JSON，不含 markdown，不含任何說明文字，格式如下：
{{
  "episode": "EP{ep_num}",
  "date": "{date}",
  "title": "EP{ep_num} | [節目標題emoji]",
  "host": "謝孟恭",
  "durationMin": 估計分鐘數整數,
  "summary": "1000-1500字繁體中文，按討論順序逐一整理每個議題，保留主持人語氣。必須包含：EPS/本益比/目標價等具體數字、主持人自身持倉揭露、核心推論邏輯鏈",
  "news": [
    {{
      "title": "議題標題",
      "category": "分類（如：被動元件/AI產業/台股總體/生活分享）",
      "sourceRef": "約X-Y分鐘",
      "event": "3-5句描述事件內容",
      "opinion": "孟公的觀點、推論與投資含義"
    }}
  ],
  "hostDisclosure": [
    {{
      "action": "買進/持有/出脫/觀望/加碼/計劃買進/降低/持有不動",
      "asset": "資產名稱",
      "quote": "逐字引用孟公原話",
      "status": "目前持倉狀態說明"
    }}
  ],
  "stockAnalysis": [
    {{
      "name": "股票或族群完整名稱",
      "sentiment": "bullish 或 watchful 或 neutral 或 bearish 或 neutral-bullish",
      "tickers": ["股票代碼，台股用 XXXX.TW，美股用標準代碼"],
      "hostOwned": false,
      "risk": "主要風險說明一句話",
      "analysis": "4-6句詳細分析，含驅動邏輯、數據支撐、孟公觀點"
    }}
  ],
  "qa": [
    {{
      "sender": "留言者名稱",
      "question": "完整還原問題內容",
      "answerPoints": ["孟公回答要點1", "要點2", "要點3"],
      "keyTakeaway": "最重要的金句或核心洞見，盡量引用原話"
    }}
  ]
}}

特別注意：
- news：從開頭到QA前，每個議題獨立一張卡片，即使只花1-2分鐘也要收錄，不要合併
- hostDisclosure：★最重要★ 孟公提到「有持有/已買入/已出清/正在加碼/計劃買進」的每一筆都要逐字引用原話
- stockAnalysis：每個被提及的個股或產業族群都要收錄
- qa：每一個聽眾提問都要收錄

逐字稿如下：

{transcript}"""


def get_new_episode():
    """從 RSS 取得最新未分析的集數，回傳 (ep_num, audio_url, pub_date) 或 None"""
    with urllib.request.urlopen(RSS_URL) as r:
        tree = ET.fromstring(r.read())
    for item in tree.findall('.//item'):
        title    = item.findtext('title', '')
        enc      = item.find('enclosure')
        audio    = enc.get('url', '') if enc is not None else ''
        pub_date = item.findtext('pubDate', '')
        m = re.search(r'EP(\d+)', title, re.IGNORECASE)
        if not m:
            continue
        ep_num = int(m.group(1))
        if not os.path.exists(os.path.join(BASE, f'ep{ep_num}_analysis.json')):
            return ep_num, audio, pub_date
    return None


def transcribe(audio_url):
    """送 AssemblyAI 轉錄，等到完成後回傳文字"""
    payload = json.dumps({
        'audio_url': audio_url,
        'speech_models': ['universal-2'],
        'language_code': 'zh'
    }).encode()
    req = urllib.request.Request(
        'https://api.assemblyai.com/v2/transcript', data=payload,
        headers={'authorization': ASSEMBLYAI_KEY, 'content-type': 'application/json'})
    tid = json.loads(urllib.request.urlopen(req).read())['id']
    print(f'  Transcript ID: {tid}')

    for i in range(80):
        req = urllib.request.Request(
            f'https://api.assemblyai.com/v2/transcript/{tid}',
            headers={'authorization': ASSEMBLYAI_KEY})
        resp = json.loads(urllib.request.urlopen(req).read())
        print(f'  [{i*15}s] {resp["status"]}')
        if resp['status'] == 'completed':
            return resp['text']
        if resp['status'] == 'error':
            raise RuntimeError(f'轉錄失敗: {resp.get("error")}')
        time.sleep(15)
    raise RuntimeError('轉錄逾時')


def analyze(transcript, ep_num, date_str):
    """呼叫 Claude API 分析逐字稿，回傳 dict"""
    try:
        import anthropic
    except ImportError:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'anthropic', '-q'], check=True)
        import anthropic

    if not ANTHROPIC_KEY:
        raise RuntimeError('未設定 ANTHROPIC_API_KEY 環境變數')

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    prompt = PROMPT_TEMPLATE.format(ep_num=ep_num, date=date_str, transcript=transcript)

    print('  呼叫 Claude API...')
    msg = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=8192,
        messages=[{'role': 'user', 'content': prompt}]
    )
    text = msg.content[0].text.strip()
    # 清除可能的 markdown 包裝
    text = re.sub(r'^```(?:json)?\n?', '', text)
    text = re.sub(r'\n?```$', '', text)
    return json.loads(text)


def update_generate_report(ep_num, date_label):
    """更新 generate_report.py 加入新集數"""
    path = os.path.join(BASE, 'generate_report.py')
    content = open(path, encoding='utf-8').read()
    ep_id = f'ep{ep_num}'

    # 1. 更新 episode 列表
    m = re.search(r'for ep in \[([^\]]*)\]:', content)
    if m:
        current_eps = re.findall(r'"(ep\d+)"', m.group(1))
        if ep_id not in current_eps:
            current_eps.append(ep_id)
            new_list = ','.join(f'"{e}"' for e in current_eps)
            content = content[:m.start()] + f'for ep in [{new_list}]:' + content[m.end():]

    # 2. 更新 TAB_LABELS（插在最後一個 ep tab 之後）
    tab_line = f'    ("{ep_id}","EP{ep_num} · {date_label}"),'
    if tab_line not in content:
        last = None
        for match in re.finditer(r'    \("ep\d+","EP\d+ · \d{2}/\d{2}"\),', content):
            last = match
        if last:
            content = content[:last.end()] + '\n' + tab_line + content[last.end():]

    open(path, 'w', encoding='utf-8').write(content)
    print(f'  generate_report.py 已更新（加入 {ep_id}）')


def main():
    result = get_new_episode()
    if not result:
        print('✓ 無新集數，略過')
        return

    ep_num, audio_url, pub_date = result
    ep_id = f'ep{ep_num}'
    print(f'\n🎙  發現 EP{ep_num}，開始自動分析')

    # 解析日期
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(pub_date)
        date_str   = dt.strftime('%Y-%m-%d')
        date_label = dt.strftime('%m/%d')
    except Exception:
        date_str   = '????-??-??'
        date_label = '??/??'

    # Step 1: 轉錄
    print('\n[1/4] 轉錄中...')
    transcript = transcribe(audio_url)
    t_path = os.path.join(BASE, f'{ep_id}_transcript.txt')
    open(t_path, 'w', encoding='utf-8').write(transcript)
    print(f'  完成：{len(transcript):,} 字')

    # Step 2: 分析
    print('\n[2/4] Claude API 分析中...')
    analysis = analyze(transcript, ep_num, date_str)
    a_path = os.path.join(BASE, f'{ep_id}_analysis.json')
    json.dump(analysis, open(a_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'  完成：{a_path}')

    # Step 3: 更新 generate_report.py
    print('\n[3/4] 更新報告腳本...')
    update_generate_report(ep_num, date_label)

    # Step 4: 生成 HTML + push
    print('\n[4/4] 生成 HTML 報告並推送...')
    subprocess.run([sys.executable, os.path.join(BASE, 'generate_report.py')],
                   check=True, cwd=BASE)

    print(f'\n✅ EP{ep_num} 分析完成！')
    print(f'   報告：https://harvey2017.github.io/Podcasts-analysis-/')


if __name__ == '__main__':
    main()
