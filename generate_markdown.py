import os
import re
import json
import unicodedata
from fontTools.ttLib import TTFont
from pypdf import PdfReader

base_dir = os.path.dirname(os.path.abspath(__file__))

# 1. Font reverse decoding setup
windir = os.environ.get('WINDIR', r'C:\Windows')
tt_path = os.path.join(windir, 'Fonts', 'kaiu.ttf')
if not os.path.exists(tt_path):
    tt_path = r'C:\Windows\Fonts\kaiu.ttf'

if os.path.exists(tt_path):
    tt = TTFont(tt_path)
    cmap = tt.getBestCmap()
    gid_to_char = {tt.getGlyphID(name): chr(code) for code, name in cmap.items()}
else:
    gid_to_char = {}

punct = {
    0x0202: '，', 0x0203: '、', 0x0204: '。', 0x0207: '；', 0x0208: '：', 0x020A: '：', 0x020C: '；', 0x020E: '？',
    0x0210: '！', 0x0218: '「', 0x0219: '」', 0x021A: '『', 0x021B: '』', 0x021C: '（', 0x021D: '）',
    0x021E: '（', 0x021F: '）', 0x0236: '「', 0x0237: '」', 0x0282: '~', 0x02A6: '%',
    0x018F: '、', 0x019D: '：', 0x019E: '：', 0x01B1: '：', 0x01F5: '-', 0x0201: '、'
}

raw_dir = os.path.join(base_dir, 'raw')
md_dir = os.path.join(base_dir, 'markdown')
graph_dir = os.path.join(base_dir, 'graph')
os.makedirs(md_dir, exist_ok=True)
os.makedirs(graph_dir, exist_ok=True)

METADATA_CONFIG = {
    '20261109_玉山投顧_ETF交易追蹤.pdf': {
        'title': '玉山投顧 ETF交易追蹤',
        'date': '2026-11-09',
        'category': 'ETF / 基金市場',
        'summary': '台股急跌後反彈，市值型承壓，資金轉進反向與債券ETF。',
        'tickers': ['0050', '009816', '00685L', '00631L', '00632R', '2330台積電'],
        'market': '台股 / ETF',
        'sentiment': '震盪偏弱',
        'theme': 'ETF資產配置與避險'
    },
    '20261109_玉山投顧_全球股債匯市暨重點產業週報.pdf': {
        'title': '玉山投顧 全球股債匯市暨重點產業週報',
        'date': '2026-11-09',
        'category': '全球市場 / 總體經濟',
        'summary': '全球股債震盪，美債殖利率升，科技回檔而防禦性資產抗跌。',
        'tickers': ['道瓊', 'S&P 500', 'NASDAQ', '美國10年期公債', '美元指數'],
        'market': '全球總經',
        'sentiment': '震盪分歧',
        'theme': '全球宏觀與利率動態'
    },
    '20261109_玉山投顧_台股(含期權)盤後分析.pdf': {
        'title': '玉山投顧 台股(含期權)盤後分析',
        'date': '2026-11-09',
        'category': '台股大盤 / 期貨選擇權',
        'summary': '國安基金與限空令激勵台股大漲千點重返4萬大關，期指翻多。',
        'tickers': ['加權指數', 'OTC指數', '台指期', '電子期', '三大法人'],
        'market': '台股大盤',
        'sentiment': '強勁反彈',
        'theme': '大盤與衍生性金融商品'
    },
    '20261109_玉山投顧_市場快訊_簡評中國10月CPI、PPI.pdf': {
        'title': '玉山投顧 市場快訊 簡評中國10月CPI、PPI',
        'date': '2026-11-09',
        'category': '大中華 / 宏觀總經',
        'summary': '中國10月CPI降至0.7%、PPI擴至5.7%，內需疲弱。',
        'tickers': ['中國CPI', '中國PPI', '核心通膨', '人行貨幣政策'],
        'market': '陸港總經',
        'sentiment': '中性保守',
        'theme': '大中華總經與通膨剪刀差'
    },
    '20261109_玉山投顧_複委託ETF週報.pdf': {
        'title': '玉山投顧 複委託ETF週報',
        'date': '2026-11-09',
        'category': '海外ETF / 複委託',
        'summary': '海外科技ETF重挫，SMH週跌逾11%，資金轉進公用與美債。',
        'tickers': ['SMH', 'SOXX', 'QQQ', 'SPY', 'XLE', 'TLT'],
        'market': '美股 / 海外ETF',
        'sentiment': '防禦避險',
        'theme': '海外ETF流向與板塊輪動'
    },
    '20261109_短線焦點產業_光通訊相關族群.pdf': {
        'title': '短線焦點產業 光通訊相關族群',
        'date': '2026-11-09',
        'category': '產業深度 / 科技硬體',
        'summary': 'AI需求帶動光通訊升級，全新、聯亞、聯鈞受惠CPO商機。',
        'tickers': ['全新(2455)', 'IET-KY(4971)', '環宇-KY(4991)', '聯亞(3081)', '光聖(6442)', '聯鈞(3450)', '華星光(4979)'],
        'market': '台股產業',
        'sentiment': '偏多看好',
        'theme': 'AI光模組與CPO矽光子'
    },
    '20261110_玉山投顧_十月份台股交易結構追蹤.pdf': {
        'title': '玉山投顧 十月份台股交易結構追蹤',
        'date': '2026-11-10',
        'category': '籌碼結構 / 市場統計',
        'summary': '10月大盤成交額增至18.5兆，週轉率升，散戶開戶續創新高。',
        'tickers': ['市場週轉率', '開戶人數', '外資買賣', '投信動向', '自然人散戶'],
        'market': '台股籌碼',
        'sentiment': '熱度維持',
        'theme': '市場資金結構與散戶參與度'
    },
    '20261110_玉山投顧_台股晨訊.pdf': {
        'title': '玉山投顧 台股晨訊',
        'date': '2026-11-10',
        'category': '盤前晨訊 / 台股焦點',
        'summary': '費半強彈帶動台股暴漲1960點收復4萬點，塑膠電子領軍。',
        'tickers': ['加權指數', '台積電(2330)', '融資餘額', '外資賣超', '塑膠股', '電子權值'],
        'market': '台股市場',
        'sentiment': '反彈偏多',
        'theme': '台股盤前與強勢族群速遞'
    },
    '20261110_玉山投顧_台股當沖速報.pdf': {
        'title': '玉山投顧 台股當沖速報',
        'date': '2026-11-10',
        'category': '短線交易 / 當日沖銷',
        'summary': '大盤強彈近2千點，當沖量占24.8%、成交值占比逾42%。',
        'tickers': ['當沖熱門標的', '當沖週轉率', '加權指數', '當沖成交值'],
        'market': '台股當沖',
        'sentiment': '短線熱絡',
        'theme': '大盤當沖熱度與周轉率'
    },
    '20261110_玉山投顧_塑化產品報價與利差週報.pdf': {
        'title': '玉山投顧 塑化產品報價與利差週報',
        'date': '2026-11-10',
        'category': '傳產原物料 / 塑化產業',
        'summary': '上游乙烯抗跌，下游PP價揚利差擴大，台塑營運相對受惠。',
        'tickers': ['台塑(1301)', '乙烯', '丙烯', 'VCM', 'PVC', 'PP'],
        'market': '原物料 / 傳產',
        'sentiment': '利差改善',
        'theme': '塑化利差與台塑受惠'
    },
    '20261110_玉山投顧_日股晨訊.pdf': {
        'title': '玉山投顧 日股晨訊',
        'date': '2026-11-10',
        'category': '國際晨訊 / 日股市場',
        'summary': '日經大漲1340點收58775點，東證收復季線，半導體領漲。',
        'tickers': ['日經225', '東證指數', '索尼(Sony)', '日立製作所', 'Kokusai Electric'],
        'market': '日股市場',
        'sentiment': '強勁反彈',
        'theme': '日股焦點與半導體設備'
    },
    '20261110_玉山投顧_港股晨訊.pdf': {
        'title': '玉山投顧 港股晨訊',
        'date': '2026-11-10',
        'category': '大中華晨訊 / 港陸市場',
        'summary': '恆生指數微跌收24448點區間震盪，上證收紅觀望政策。',
        'tickers': ['恆生指數', '恆生國企', '上證指數', '滬深300', '長鑫存儲(CXMT)', '韋爾股份'],
        'market': '港陸市場',
        'sentiment': '區間整理',
        'theme': '港滬盤勢與半導體供應鏈'
    },
    '20261110_玉山投顧_研究報告_8081致新_中立_維持.pdf': {
        'title': '玉山投顧 研究報告 8081致新 中立 維持',
        'date': '2026-11-10',
        'category': '個股研究 / 半導體IC',
        'summary': '致新PMIC競爭大，NB需求平穩，維持中立與目標價270。',
        'tickers': ['致新(8081)', '電源管理IC (PMIC)', 'PC/NB應用', '毛利率', '目標價270元'],
        'market': '台股個股',
        'sentiment': '中立',
        'theme': 'IC設計與個股評價'
    },
    '20261110_玉山投顧_美股晨訊.pdf': {
        'title': '玉山投顧 美股晨訊',
        'date': '2026-11-10',
        'category': '國際晨訊 / 美股市場',
        'summary': '費半狂飆6.9%、那指漲2.7%，科技巨頭領軍報復性反彈。',
        'tickers': ['道瓊工業', 'S&P 500', 'NASDAQ', '費城半導體', '蘋果(AAPL)', '輝達(NVDA)', '微軟(MSFT)'],
        'market': '美股市場',
        'sentiment': '強勁大漲',
        'theme': '美股巨頭與半導體強彈'
    },
    '20261110台股_投資快訊_今日五檔焦點股.pdf': {
        'title': '台股投資快訊 今日五檔焦點股',
        'date': '2026-11-10',
        'category': '個股推薦 / 投資快訊',
        'summary': '世芯、營邦、聯發科、中砂、群聯獲利看增，技術面轉強反彈。',
        'tickers': ['世芯-KY(3661)', '營邦(3693)', '聯發科(2454)', '中砂(1560)', '群聯(8299)'],
        'market': '台股焦點股',
        'sentiment': '強勢看多',
        'theme': '短線強勢股與技術指標'
    }
}

disclaimer_patterns = [
    r'本公司已針對報告內容力求正確.*?(須經本公司同意[。Ȅ]?)',
    r'本公司已針對報告內容力求正確.*?(不負任何投資盈虧之法律責任[。Ȅ]?)',
    r'本公司已針對報告內容力求正確.*?\n',
    r'如引用本文.*?須經本公司同意[。Ȅ]?',
    r'僅供投資人參考.*?法律責任[。Ȅ]?'
]

def decode_cid_text(raw_text):
    out = []
    for ch in raw_text:
        cid = ord(ch)
        if cid in punct:
            out.append(punct[cid])
        elif 0x0370 <= cid <= 0x1FFF:
            char = gid_to_char.get(cid - 15, gid_to_char.get(cid - 14, gid_to_char.get(cid, ch)))
            out.append(char)
        else:
            out.append(ch)
    return ''.join(out)

def clean_text(text):
    text = unicodedata.normalize('NFKC', text)
    # Common OCR/PDF text substitutions
    text = text.replace('㠈生指數', '恆生指數').replace('㠈生', '恆生')
    # Remove disclaimer variations
    disclaimers = [
        r'本公司已針對報告內容力求正確.*?(須經本公司同意[。.]?)',
        r'本公司已針對報告內容力求正確.*?(不負任何投資盈虧之法律責任[。.]?)',
        r'如引用本文.*?須經本公司同意[。.]?',
        r'僅供投資人參考.*?法律責任[。.]?',
        r'本公司不負任何投資盈虧之法律責任[。.]?'
    ]
    for pat in disclaimers:
        text = re.sub(pat, '', text, flags=re.DOTALL)
        
    # Remove recurring empty header dates / single page number artifacts
    text = re.sub(r'^\s*2026/11/\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[Ee]\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'E\.SUN\s+Investment\s+Consulting', '', text, flags=re.IGNORECASE)
    # Normalize multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def format_tables_and_headings(text):
    lines = text.split('\n')
    processed_lines = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            processed_lines.append('')
            continue
            
        # Detect headings
        if stripped.startswith('| ') or stripped.startswith('◼') or stripped.startswith('') or stripped.startswith('„'):
            clean_head = stripped.lstrip('|◼„ ').strip()
            # If it's a major section heading
            if any(k in clean_head for k in ['主要指數', '前言', '盤勢及焦點', '財務狀況', '大盤成交值', '產品報價', '大盤當沖資訊', '評等', '營運']):
                processed_lines.append(f'\n### {clean_head}\n')
            else:
                processed_lines.append(f'- **{clean_head}**')
        elif re.match(r'^[A-Za-z0-9\-\u4e00-\u9fff]+\s*\(\d{4}\)', stripped):
            # Stock section like 世芯-KY(3661)-短線槓桿
            processed_lines.append(f'\n## {stripped}\n')
        elif re.match(r'^(指\s*數|股名|代\s*號|法人別|日期|大盤|產品名稱)\s+', stripped):
            # Potential table header
            cols = [c.strip() for c in re.split(r'\s{2,}|\t', stripped) if c.strip()]
            if len(cols) >= 3:
                header_row = '| ' + ' | '.join(cols) + ' |'
                sep_row = '| ' + ' | '.join(['---'] * len(cols)) + ' |'
                processed_lines.append(header_row)
                processed_lines.append(sep_row)
            else:
                processed_lines.append(stripped)
        elif re.search(r'\d+\.\d+\s+\d+', stripped):
            # Potential table data row
            cols = [c.strip() for c in re.split(r'\s{2,}|\t', stripped) if c.strip()]
            if len(cols) >= 3:
                processed_lines.append('| ' + ' | '.join(cols) + ' |')
            else:
                processed_lines.append(stripped)
        else:
            processed_lines.append(stripped)
            
    res = '\n'.join(processed_lines)
    res = re.sub(r'\n{3,}', '\n\n', res)
    return res

summaries_list = []

for pdf_name, meta in sorted(METADATA_CONFIG.items()):
    pdf_path = os.path.join(raw_dir, pdf_name)
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    
    is_morning = '晨訊' in pdf_name
    pages_content = []
    
    for idx, page in enumerate(reader.pages):
        raw_text = page.extract_text() or ''
        if is_morning:
            page_text = decode_cid_text(raw_text)
        else:
            page_text = raw_text
        pages_content.append(page_text)
        
    full_content = '\n\n'.join(pages_content)
    cleaned = clean_text(full_content)
    formatted_body = format_tables_and_headings(cleaned)
    
    md_filename = pdf_name.replace('.pdf', '.md')
    md_path = os.path.join(md_dir, md_filename)
    
    # Construct complete markdown document
    frontmatter = f"""---
title: "{meta['title']}"
date: {meta['date']}
source_file: "{pdf_name}"
pages: {total_pages}
category: "{meta['category']}"
market: "{meta['market']}"
theme: "{meta['theme']}"
sentiment: "{meta['sentiment']}"
tickers: {json.dumps(meta['tickers'], ensure_ascii=False)}
summary: "{meta['summary']}"
---

# {meta['title']}

> **【30字精準摘要】**：{meta['summary']}

| 報告屬性 | 說明 |
| :--- | :--- |
| **發布日期** | {meta['date']} |
| **報告分類** | {meta['category']} |
| **核心市場** | {meta['market']} |
| **主題標籤** | {meta['theme']} |
| **多空態度** | `{meta['sentiment']}` |
| **重點標的** | {', '.join(meta['tickers'])} |
| **原始頁數** | {total_pages} 頁 |

---

## 報告內容解析

{formatted_body}

---
*本文件由投顧報告解析系統由原始 PDF 自動轉換而成，保留完整數值、結構與分析觀點。*
"""
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
        
    print(f'Generated: {md_filename} ({total_pages} pages)')
    
    summaries_list.append({
        'filename': pdf_name,
        'md_filename': md_filename,
        'title': meta['title'],
        'date': meta['date'],
        'category': meta['category'],
        'market': meta['market'],
        'theme': meta['theme'],
        'sentiment': meta['sentiment'],
        'summary': meta['summary'],
        'summary_length': len(meta['summary']),
        'tickers': meta['tickers'],
        'pages': total_pages
    })

# Save summaries.json
with open(os.path.join(base_dir, 'summaries.json'), 'w', encoding='utf-8') as f:
    json.dump(summaries_list, f, ensure_ascii=False, indent=2)

print('Saved summaries.json')
