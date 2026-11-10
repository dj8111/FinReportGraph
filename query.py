"""
投顧報告知識圖譜與摘要查詢工具 (Investment Report Query Tool)
支援快速查詢個股、標的、產業、市場、多空態度與報告摘要。
"""

import sys
import os
import json
import argparse

base_dir = os.path.dirname(os.path.abspath(__file__))
kg_path = os.path.join(base_dir, 'graph', 'knowledge_graph.json')
summaries_path = os.path.join(base_dir, 'summaries.json')

with open(kg_path, 'r', encoding='utf-8') as f:
    kg = json.load(f)

with open(summaries_path, 'r', encoding='utf-8') as f:
    summaries = json.load(f)

nodes = {n['id']: n for n in kg['nodes']}
links = kg['links']

def list_all_summaries():
    print("\n" + "=" * 90)
    print(" 📑 15 份投顧研究報告精選 30 字摘要總覽")
    print("=" * 90)
    for idx, s in enumerate(summaries, 1):
        print(f"[{idx:2}] {s['date']} | {s['title']}")
        print(f"     分類: {s['category']:18} | 態度: {s['sentiment']:6} | 頁數: {s['pages']:2} 頁")
        print(f"     標的: {', '.join(s['tickers'][:5])}")
        print(f"     📌 摘要 ({len(s['summary'])}字): {s['summary']}")
        print(f"     📄 檔案: markdown/{s['md_filename']}")
        print("-" * 90)

def search_query(keyword):
    kw = keyword.strip().lower()
    print(f"\n🔍 查詢關鍵字: 「{keyword}」")
    print("=" * 90)
    
    # Match in nodes
    matched_nodes = []
    for n_id, n in nodes.items():
        if kw in n['name'].lower() or (n['description'] and kw in n['description'].lower()):
            matched_nodes.append(n)
            
    if matched_nodes:
        print(f"📍 找到 {len(matched_nodes)} 個相關節點 (知識圖譜):")
        for n in matched_nodes:
            print(f"  • [{n['category']}] {n['name']}")
            if n['description']:
                print(f"    說明/摘要: {n['description']}")
            if n['link']:
                print(f"    文檔連結: {n['link']}")
                
            # Find connections
            connected_edges = [l for l in links if l['source'] == n['id'] or l['target'] == n['id']]
            if connected_edges:
                conn_strs = []
                for e in connected_edges[:6]:
                    other_id = e['target'] if e['source'] == n['id'] else e['source']
                    other_name = nodes.get(other_id, {}).get('name', other_id)
                    conn_strs.append(f"{other_name} ({e['relation']})")
                print(f"    關聯節點: {', '.join(conn_strs)}")
            print()
    else:
        print("❌ 知識圖譜中未直接匹配到節點名稱。")
        
    # Match in report contents
    print("-" * 90)
    print("📄 報告摘要與標的匹配:")
    matched_reports = []
    for s in summaries:
        in_tickers = any(kw in t.lower() for t in s['tickers'])
        in_summary = kw in s['summary'].lower()
        in_title = kw in s['title'].lower()
        if in_tickers or in_summary or in_title:
            matched_reports.append(s)
            
    if matched_reports:
        for r in matched_reports:
            print(f"  • {r['date']} | {r['title']} [{r['category']}]")
            print(f"    態度: {r['sentiment']} | 提及標的: {', '.join(r['tickers'])}")
            print(f"    摘要: {r['summary']}")
            print(f"    開啟: markdown/{r['md_filename']}\n")
    else:
        print("❌ 未在報告標籤與摘要中找到匹配項。")
    print("=" * 90)

def filter_market(mkt_keyword):
    print(f"\n🌐 篩選市場板塊: 「{mkt_keyword}」")
    print("=" * 90)
    for s in summaries:
        if mkt_keyword.lower() in s['market'].lower() or mkt_keyword.lower() in s['category'].lower():
            print(f"• {s['date']} | {s['title']} ({s['market']})")
            print(f"  摘要: {s['summary']}")
            print(f"  標的: {', '.join(s['tickers'])}")
            print(f"  連結: markdown/{s['md_filename']}\n")

def show_top_picks():
    print("\n" + "=" * 90)
    print(" 🚀 今日五大精選焦點股與致新目標價評析速查")
    print("=" * 90)
    picks = [
        {"name": "世芯-KY (3661)", "type": "短線槓桿", "support": "2,670 元", "resistance": "4,500 元", "thesis": "3nm AI 加速器放量，美系 CSP 客戶年貢獻上看 10 億美元，日KD黃金交叉。"},
        {"name": "營邦 (3693)", "type": "短線槓桿", "support": "480 元", "resistance": "660 元", "thesis": "AMD Helios AI 機櫃量產直供北美雲端巨頭，10月營收衝19.7億年增231%。"},
        {"name": "聯發科 (2454)", "type": "短線槓桿", "support": "3,200 元", "resistance": "4,200 元", "thesis": "首款雲端 AI ASIC 2027營收挑戰160億美元，天璣9600 Pro 2nm旗艦機晶片。"},
        {"name": "中砂 (1560)", "type": "波段操作", "support": "640 元", "resistance": "900 元", "thesis": "台積電 2nm 鑽石碟月產能上看 10 萬顆，CoWoS/HBM 研磨新品出貨。"},
        {"name": "群聯 (8299)", "type": "波段操作", "support": "1,400 元", "resistance": "1,860 元", "thesis": "企業級 SSD 控制晶片量產，邊緣 AI 落地爆發，評價落入超賣低檔區。"},
        {"name": "致新 (8081)", "type": "中立·維持", "support": "收盤 235.5 元", "resistance": "目標價 270 元", "thesis": "PMIC 同業競爭激烈，NB/PC 需求持平，毛利率承壓，維持中立評等。"}
    ]
    for p in picks:
        print(f"⭐ {p['name']} [{p['type']}]")
        print(f"   支撐: {p['support']:12} | 壓力/目標: {p['resistance']:12}")
        print(f"   亮點: {p['thesis']}\n")

def main():
    parser = argparse.ArgumentParser(description="玉山投顧報告知識庫查詢工具")
    parser.add_argument("query", nargs="?", help="查詢標的、個股代碼或關鍵字 (例：台積電、3661、光通訊、CPO、費半)")
    parser.add_argument("--list", "-l", action="store_true", help="列出全部 15 份報告 30 字摘要")
    parser.add_argument("--market", "-m", help="依市場或分類篩選 (例：台股、美股、日股、港陸、ETF)")
    parser.add_argument("--picks", "-p", action="store_true", help="檢視今日焦點股 (世芯/聯發科/中砂/營邦/群聯/致新)")
    args = parser.parse_args()

    if args.list:
        list_all_summaries()
    elif args.market:
        filter_market(args.market)
    elif args.picks:
        show_top_picks()
    elif args.query:
        search_query(args.query)
    else:
        print("💡 請輸入查詢關鍵字，或使用參數：")
        print("   python query.py 3661             # 查詢世芯-KY")
        print("   python query.py 台積電           # 查詢台積電相關報告與關係")
        print("   python query.py 光通訊           # 查詢光通訊族群與CPO標的")
        print("   python query.py --picks          # 檢視今日五檔焦點股與目標價")
        print("   python query.py --market 美股    # 篩選美股相關報告")
        print("   python query.py --list           # 列出全部 15 份報告之 30 字摘要")

if __name__ == '__main__':
    main()

