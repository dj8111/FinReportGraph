import os
import json
import re

base_dir = os.path.dirname(os.path.abspath(__file__))
graph_dir = os.path.join(base_dir, 'graph')
os.makedirs(graph_dir, exist_ok=True)
summaries_path = os.path.join(base_dir, 'summaries.json')
with open(summaries_path, 'r', encoding='utf-8') as f:
    summaries = json.load(f)

# 1. Build README.md and 00_報告目錄與摘要彙整.md
readme_content = f"""# 投顧研究報告知識庫系統

本專案將 `raw/` 目錄下的 15 份專業投顧 PDF 研究報告完整拆解轉化為結構化 Markdown 文檔、提煉 30 字以內核心摘要，並建構跨市場與產業的互動式知識圖表。

---

## 📌 報告目錄與 30 字精準摘要彙整表

| # | 日期 | 報告名稱 (Markdown連結) | 分類 | 30字精準摘要 | 態度 | 核心標的 / 代碼 |
|:---:|:---:|:---|:---|:---|:---:|:---|
"""

for idx, item in enumerate(summaries, 1):
    md_link = f"[{item['title']}](markdown/{item['md_filename']})"
    tickers_str = ", ".join(item['tickers'])
    readme_content += f"| {idx} | {item['date']} | {md_link} | {item['category']} | {item['summary']} | `{item['sentiment']}` | {tickers_str} |\n"

readme_content += """
---

## 📊 知識圖表與導航

- 🌐 **[互動式知識圖譜 (瀏覽器直接開啟)](graph/knowledge_graph.html)**：支援節點拖曳、點擊查詢、標的連線、多空態度過濾與 Markdown 文檔直達跳轉。
- 📑 **[知識圖譜結構說明與 Mermaid 關聯圖](KNOWLEDGE_MAP.md)**：包含完整實體關係矩陣與 Mermaid 心智圖。
- 💾 **[知識圖譜原始資料 (JSON)](graph/knowledge_graph.json)**：可直接供 GraphRAG、向量檢索與自動化程式呼叫。
- 📋 **[原始摘要列表 (JSON)](summaries.json)**：提供全報告元資料與 30 字摘要標準資料集。

---

## 📂 目錄架構

```
FinReportGraph/
├── raw/                         # 原始 15 份投顧 PDF 報告
├── markdown/                    # 完整解析後的結構化 Markdown 文檔 (15 篇)
├── graph/
│   ├── knowledge_graph.html     # 互動式知識圖譜可視化 (單檔即開即用)
│   └── knowledge_graph.json     # 實體與關聯三元組資料集
├── summaries.json               # 15 份文檔之 30 字摘要與元資料
├── README.md                    # 專案首頁與摘要彙整總表
└── KNOWLEDGE_MAP.md             # 知識圖表專屬架構圖與查詢索引
```
"""

with open(os.path.join(base_dir, 'README.md'), 'w', encoding='utf-8') as f:
    f.write(readme_content)

with open(os.path.join(base_dir, '00_報告目錄與摘要彙整.md'), 'w', encoding='utf-8') as f:
    f.write(readme_content)

print('Generated README.md and 00_報告目錄與摘要彙整.md')

# 2. Build Knowledge Graph (nodes and links)
# Node Categories:
# 0: 市場板塊 (Market)
# 1: 投顧報告 (Report)
# 2: 產業族群 (Industry)
# 3: 核心個股/標的 (Ticker)
# 4: 投資觀點/主題 (Theme/Insight)

nodes = []
links = []
node_set = set()

def add_node(node_id, name, category, group, desc="", link="", value=20):
    if node_id not in node_set:
        node_set.add(node_id)
        nodes.append({
            "id": node_id,
            "name": name,
            "category": category,
            "group": group,
            "value": value,
            "description": desc,
            "link": link
        })

def add_link(source, target, relation, desc=""):
    links.append({
        "source": source,
        "target": target,
        "relation": relation,
        "description": desc
    })

# Define Market Hub Nodes
markets = [
    ("mkt_tw", "台股市場", "市場板塊", 0, "涵蓋加權指數、OTC、期權與當沖籌碼", 35),
    ("mkt_us", "美股市場", "市場板塊", 0, "涵蓋美股四大指數、科技巨頭與美債", 35),
    ("mkt_jp", "日股市場", "市場板塊", 0, "日經225、東證指數與日系半導體設備", 30),
    ("mkt_hk_cn", "港陸市場", "市場板塊", 0, "恆生指數、上證指數與大中華供應鏈", 30),
    ("mkt_macro", "全球總經", "市場板塊", 0, "利率、通膨、匯市與跨資產配置", 32),
    ("mkt_etf", "ETF資產", "市場板塊", 0, "國內外市值型、主題型、槓桿反向ETF", 30),
    ("mkt_ind", "焦點產業", "市場板塊", 0, "光通訊CPO、塑化原料、先進封裝", 32)
]

for m_id, name, cat, grp, desc, val in markets:
    add_node(m_id, name, cat, grp, desc, "", val)

# Industries
industries = [
    ("ind_semi", "半導體與先進封裝", "產業族群", 2, "2nm/3nm製程、CoWoS、HBM與IC設計", 25),
    ("ind_optical", "光通訊與CPO", "產業族群", 2, "800G/1.6T光收發模組、矽光子與化合物半導體磊晶", 25),
    ("ind_chemical", "塑化原物料", "產業族群", 2, "乙烯、丙烯、VCM、PVC與PP利差受惠", 22),
    ("ind_ai_server", "AI伺服器與儲存", "產業族群", 2, "AI ASIC機櫃、高階儲存系統與機殼整合", 24),
    ("ind_finance", "期權與籌碼衍生品", "產業族群", 2, "台指期、選擇權未平倉與當日沖銷流動性", 20)
]

for i_id, name, cat, grp, desc, val in industries:
    add_node(i_id, name, cat, grp, desc, "", val)
    if "半導體" in name or "光通訊" in name or "AI" in name:
        add_link("mkt_ind", i_id, "包含產業")
        add_link("mkt_tw", i_id, "台股核心供應鏈")
    elif "塑化" in name:
        add_link("mkt_ind", i_id, "包含產業")
    elif "期權" in name:
        add_link("mkt_tw", i_id, "交易機制")

# Connect reports and their specific targets
for r in summaries:
    r_id = "rep_" + r['md_filename'].replace('.md', '')
    add_node(r_id, r['title'], "投顧報告", 1, r['summary'], f"markdown/{r['md_filename']}", 26)
    
    # Connect report to Market
    if '台股' in r['market']:
        add_link("mkt_tw", r_id, "涵蓋報告")
    if '美股' in r['market']:
        add_link("mkt_us", r_id, "涵蓋報告")
    if '日股' in r['market']:
        add_link("mkt_jp", r_id, "涵蓋報告")
    if '陸港' in r['market'] or '港陸' in r['market']:
        add_link("mkt_hk_cn", r_id, "涵蓋報告")
    if '總經' in r['market']:
        add_link("mkt_macro", r_id, "涵蓋報告")
    if 'ETF' in r['market']:
        add_link("mkt_etf", r_id, "涵蓋報告")
        
    # Connect to tickers
    for t in r['tickers']:
        clean_t = t.replace(' ', '')
        t_id = "tck_" + re.sub(r'[^A-Za-z0-9\u4e00-\u9fff]', '_', clean_t).strip('_')
        add_node(t_id, clean_t, "核心標的", 3, f"提及於報告：{r['title']}", f"markdown/{r['md_filename']}", 16)
        add_link(r_id, t_id, "研究分析", f"摘要：{r['summary']}")
        
        # Link tickers to industries
        if any(k in clean_t for k in ['台積電', '世芯', '聯發科', '中砂', '致新', '群聯', 'SMH', 'SOXX', '費城半導體']):
            add_link(t_id, "ind_semi", "產業歸屬")
        elif any(k in clean_t for k in ['全新', '聯亞', '聯鈞', '光聖', '華星光', 'IET', '環宇']):
            add_link(t_id, "ind_optical", "產業歸屬")
        elif any(k in clean_t for k in ['台塑', '乙烯', '丙烯', 'VCM', 'PVC', 'PP']):
            add_link(t_id, "ind_chemical", "產業歸屬")
        elif any(k in clean_t for k in ['營邦']):
            add_link(t_id, "ind_ai_server", "產業歸屬")
        elif any(k in clean_t for k in ['0050', '009816', '00685L', '00631L', '00632R', 'QQQ', 'SPY', 'TLT']):
            add_link(t_id, "mkt_etf", "資產類型")

# Additional Investment Themes & Strategic Insights
themes = [
    ("thm_nsf", "國安基金與限空令", "投資觀點", 4, "政策利多激勵台股自4萬點強彈1960點", 22),
    ("thm_2nm_3nm", "2nm/3nm先進製程", "投資觀點", 4, "台積電擴產帶動世芯、中砂、聯發科", 22),
    ("thm_cpo", "CPO與800G光模組", "投資觀點", 4, "AI資料中心算力激增帶動光通訊傳輸升級", 22),
    ("thm_dt_heat", "台股當沖熱度升溫", "投資觀點", 4, "當沖成交值占比逾42%，散戶開戶續創新高", 20),
    ("thm_us_bounce", "費半報復性強彈", "投資觀點", 4, "費半狂飆6.9%，科技股短線利空出盡翻多", 20),
    ("thm_cn_deflation", "中國通膨剪刀差", "投資觀點", 4, "CPI回落至0.7%、PPI擴至5.7%，反映內需偏弱", 20)
]

for th_id, name, cat, grp, desc, val in themes:
    add_node(th_id, name, cat, grp, desc, "", val)

# Connect themes to specific reports/tickers
add_link("thm_nsf", "rep_20261109_玉山投顧_台股(含期權)盤後分析", "核心驅動力")
add_link("thm_nsf", "rep_20261110_玉山投顧_台股晨訊", "核心驅動力")
add_link("thm_2nm_3nm", "tck_世芯_KY_3661_", "關鍵成長引擎")
add_link("thm_2nm_3nm", "tck_中砂_1560_", "關鍵成長引擎")
add_link("thm_2nm_3nm", "tck_聯發科_2454_", "關鍵成長引擎")
add_link("thm_cpo", "ind_optical", "關鍵技術演進")
add_link("thm_dt_heat", "rep_20261110_玉山投顧_台股當沖速報", "核心論點")
add_link("thm_dt_heat", "rep_20261110_玉山投顧_十月份台股交易結構追蹤", "核心論點")
add_link("thm_us_bounce", "rep_20261110_玉山投顧_美股晨訊", "核心走勢")
add_link("thm_cn_deflation", "rep_20261109_玉山投顧_市場快訊_簡評中國10月CPI_PPI", "宏觀結論")

# Save knowledge_graph.json
kg_data = {
    "categories": [
        {"name": "市場板塊", "color": "#1976D2"},
        {"name": "投顧報告", "color": "#7B1FA2"},
        {"name": "產業族群", "color": "#388E3C"},
        {"name": "核心標的", "color": "#F57C00"},
        {"name": "投資觀點", "color": "#D32F2F"}
    ],
    "nodes": nodes,
    "links": links
}

with open(os.path.join(graph_dir, 'knowledge_graph.json'), 'w', encoding='utf-8') as f:
    json.dump(kg_data, f, ensure_ascii=False, indent=2)

print(f"Generated knowledge_graph.json ({len(nodes)} nodes, {len(links)} links)")

# 3. Build standalone HTML visualization (using ECharts via CDN with embedded fallback styling)
html_template = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>玉山投顧研究報告 - 互動式知識圖譜</title>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      display: flex;
      height: 100vh;
      overflow: hidden;
    }}
    #sidebar {{
      width: 360px;
      background: #1e293b;
      border-right: 1px solid #334155;
      display: flex;
      flex-direction: column;
      z-index: 10;
      box-shadow: 4px 0 24px rgba(0,0,0,0.4);
    }}
    .sidebar-header {{
      padding: 20px;
      border-bottom: 1px solid #334155;
      background: #0f172a;
    }}
    .sidebar-header h1 {{
      font-size: 1.25rem;
      color: #38bdf8;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .sidebar-header p {{
      font-size: 0.8rem;
      color: #94a3b8;
      margin-top: 6px;
      line-height: 1.4;
    }}
    .search-box {{
      padding: 12px 20px;
      border-bottom: 1px solid #334155;
    }}
    .search-box input {{
      width: 100%;
      padding: 10px 14px;
      border-radius: 8px;
      border: 1px solid #475569;
      background: #0f172a;
      color: #f8fafc;
      font-size: 0.88rem;
      outline: none;
      transition: border 0.2s;
    }}
    .search-box input:focus {{
      border-color: #38bdf8;
    }}
    .filter-pills {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      padding: 12px 20px;
      border-bottom: 1px solid #334155;
    }}
    .pill {{
      font-size: 0.75rem;
      padding: 4px 10px;
      border-radius: 12px;
      cursor: pointer;
      background: #334155;
      color: #cbd5e1;
      transition: all 0.2s;
      border: 1px solid transparent;
    }}
    .pill.active {{
      background: #0284c7;
      color: #ffffff;
      font-weight: bold;
    }}
    #details-panel {{
      flex: 1;
      padding: 20px;
      overflow-y: auto;
    }}
    .empty-state {{
      text-align: center;
      color: #64748b;
      margin-top: 60px;
      font-size: 0.9rem;
      line-height: 1.8;
    }}
    .detail-card {{
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 10px;
      padding: 18px;
      animation: fadeIn 0.25s ease-in-out;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(6px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    .detail-tag {{
      display: inline-block;
      font-size: 0.72rem;
      padding: 3px 8px;
      border-radius: 4px;
      background: #0369a1;
      color: #e0f2fe;
      margin-bottom: 10px;
      font-weight: 600;
    }}
    .detail-title {{
      font-size: 1.15rem;
      font-weight: 700;
      color: #f1f5f9;
      margin-bottom: 12px;
      line-height: 1.4;
    }}
    .detail-summary {{
      background: #1e293b;
      border-left: 3px solid #38bdf8;
      padding: 10px 12px;
      font-size: 0.88rem;
      color: #e2e8f0;
      margin-bottom: 14px;
      border-radius: 0 6px 6px 0;
      line-height: 1.5;
    }}
    .detail-desc {{
      font-size: 0.82rem;
      color: #94a3b8;
      line-height: 1.5;
      margin-bottom: 16px;
    }}
    .detail-btn {{
      display: inline-block;
      width: 100%;
      text-align: center;
      background: linear-gradient(135deg, #0284c7, #2563eb);
      color: white;
      text-decoration: none;
      padding: 10px 14px;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 600;
      transition: transform 0.15s, box-shadow 0.15s;
    }}
    .detail-btn:hover {{
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4);
    }}
    #chart-container {{
      flex: 1;
      position: relative;
    }}
    .legend-panel {{
      position: absolute;
      top: 16px;
      right: 16px;
      background: rgba(30, 41, 59, 0.85);
      backdrop-filter: blur(8px);
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 12px 16px;
      font-size: 0.8rem;
      z-index: 5;
    }}
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 6px;
    }}
    .legend-item:last-child {{ margin-bottom: 0; }}
    .legend-dot {{
      width: 12px;
      height: 12px;
      border-radius: 50%;
    }}
  </style>
</head>
<body>
  <div id="sidebar">
    <div class="sidebar-header">
      <h1>📈 投顧報告知識圖譜</h1>
      <p>涵蓋 15 份玉山投顧報告、7 大市場/板塊、5 大核心產業族群與重要個股焦點。</p>
    </div>
    <div class="search-box">
      <input type="text" id="searchInput" placeholder="🔍 搜尋標的、個股 (例：台積電、世芯、費半)..." />
    </div>
    <div class="filter-pills">
      <div class="pill active" data-category="ALL">全部</div>
      <div class="pill" data-category="市場板塊">市場板塊</div>
      <div class="pill" data-category="投顧報告">投顧報告</div>
      <div class="pill" data-category="產業族群">產業族群</div>
      <div class="pill" data-category="核心標的">核心標的</div>
      <div class="pill" data-category="投資觀點">投資觀點</div>
    </div>
    <div id="details-panel">
      <div class="empty-state">
        👆 點擊圖譜中的任意節點<br>即可在此處檢視 30 字摘要、分析觀點<br>並可直接開啟完整 Markdown 文件
      </div>
    </div>
  </div>

  <div id="chart-container">
    <div class="legend-panel">
      <div class="legend-item"><div class="legend-dot" style="background:#1976D2;"></div> 市場板塊 (7)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#7B1FA2;"></div> 投顧報告 (15)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#388E3C;"></div> 產業族群 (5)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#F57C00;"></div> 核心標的/個股 (45+)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#D32F2F;"></div> 投資觀點/主題 (6)</div>
    </div>
    <div id="main" style="width: 100%; height: 100%;"></div>
  </div>

  <script>
    const graphData = {json.dumps(kg_data, ensure_ascii=False)};
    const chartDom = document.getElementById('main');
    const myChart = echarts.init(chartDom);

    const categories = graphData.categories;
    const colorMap = {{
      "市場板塊": "#1976D2",
      "投顧報告": "#7B1FA2",
      "產業族群": "#388E3C",
      "核心標的": "#F57C00",
      "投資觀點": "#D32F2F"
    }};

    const formattedNodes = graphData.nodes.map(n => ({{
      id: n.id,
      name: n.name,
      category: n.category,
      symbolSize: n.value,
      value: n.value,
      description: n.description,
      link: n.link,
      itemStyle: {{
        color: colorMap[n.category] || '#94a3b8',
        borderColor: '#ffffff',
        borderWidth: n.category === '投顧報告' ? 2 : 1
      }},
      label: {{
        show: n.value > 18,
        fontSize: n.value > 25 ? 12 : 10,
        color: '#f8fafc'
      }}
    }}));

    const formattedLinks = graphData.links.map(l => ({{
      source: l.source,
      target: l.target,
      label: {{
        show: false,
        formatter: l.relation,
        fontSize: 9,
        color: '#94a3b8'
      }},
      lineStyle: {{
        color: '#475569',
        curveness: 0.15,
        width: 1.2,
        opacity: 0.7
      }}
    }}));

    const option = {{
      backgroundColor: '#0f172a',
      tooltip: {{
        trigger: 'item',
        formatter: function (params) {{
          if (params.dataType === 'node') {{
            return `<b>[${{params.data.category}}] ${{params.data.name}}</b><br/>${{params.data.description || ''}}`;
          }} else if (params.dataType === 'edge') {{
            return `<b>關係：${{params.data.relation || '關聯'}}</b><br/>${{params.data.description || ''}}`;
          }}
        }}
      }},
      series: [{{
        type: 'graph',
        layout: 'force',
        data: formattedNodes,
        links: formattedLinks,
        categories: categories,
        roam: true,
        label: {{
          position: 'right',
          formatter: '{{b}}'
        }},
        labelLayout: {{
          hideOverlap: true
        }},
        scaleLimit: {{
          min: 0.4,
          max: 4
        }},
        lineStyle: {{
          color: 'source',
          curveness: 0.2
        }},
        emphasis: {{
          focus: 'adjacency',
          lineStyle: {{
            width: 3.5,
            color: '#38bdf8'
          }}
        }},
        force: {{
          repulsion: 260,
          edgeLength: [60, 140],
          gravity: 0.12
        }}
      }}]
    }};

    myChart.setOption(option);

    window.addEventListener('resize', () => myChart.resize());

    // Click handler for details panel
    myChart.on('click', function (params) {{
      if (params.dataType === 'node') {{
        showNodeDetails(params.data);
      }}
    }});

    function showNodeDetails(data) {{
      const panel = document.getElementById('details-panel');
      let linkBtn = '';
      if (data.link) {{
        linkBtn = `<a href="../${{data.link}}" target="_blank" class="detail-btn">📄 開啟完整 Markdown 文檔</a>`;
      }}
      panel.innerHTML = `
        <div class="detail-card">
          <span class="detail-tag" style="background: ${{colorMap[data.category]}}">${{data.category}}</span>
          <div class="detail-title">${{data.name}}</div>
          ${{data.description ? `<div class="detail-summary"><b>摘要 / 說明：</b><br/>${{data.description}}</div>` : ''}}
          ${{linkBtn}}
        </div>
      `;
    }}

    // Filter pills
    document.querySelectorAll('.filter-pills .pill').forEach(pill => {{
      pill.addEventListener('click', function() {{
        document.querySelectorAll('.filter-pills .pill').forEach(p => p.classList.remove('active'));
        this.classList.add('active');
        const cat = this.getAttribute('data-category');
        
        const filteredNodes = formattedNodes.map(n => {{
          const isMatch = (cat === 'ALL' || n.category === cat);
          return {{
            ...n,
            itemStyle: {{
              ...n.itemStyle,
              opacity: isMatch ? 1 : 0.15
            }},
            label: {{
              ...n.label,
              show: isMatch && n.value > 18
            }}
          }};
        }});

        myChart.setOption({{
          series: [{{
            data: filteredNodes
          }}]
        }});
      }});
    }});

    // Search bar
    document.getElementById('searchInput').addEventListener('input', function(e) {{
      const term = e.target.value.trim().toLowerCase();
      if (!term) {{
        myChart.setOption({{ series: [{{ data: formattedNodes }}] }});
        return;
      }}
      const searchNodes = formattedNodes.map(n => {{
        const isMatch = n.name.toLowerCase().includes(term) || (n.description && n.description.toLowerCase().includes(term));
        return {{
          ...n,
          itemStyle: {{
            ...n.itemStyle,
            opacity: isMatch ? 1 : 0.1
          }},
          label: {{
            ...n.label,
            show: isMatch
          }}
        }};
      }});
      myChart.setOption({{ series: [{{ data: searchNodes }}] }});
    }});
  </script>
</body>
</html>
"""

with open(os.path.join(graph_dir, 'knowledge_graph.html'), 'w', encoding='utf-8') as f:
    f.write(html_template)

print('Generated graph/knowledge_graph.html')

# 4. Build KNOWLEDGE_MAP.md
km_content = """# 投顧研究報告全域知識圖譜 (Knowledge Map)

本文件以結構化矩陣與 Mermaid 視覺化圖表，呈現 15 份玉山投顧報告之市場板塊、產業族群、核心個股與投資觀點。

---

## 🗺️ 跨市場總體架構圖 (Mermaid Architecture)

```mermaid
graph TD
    classDef market fill:#1976D2,stroke:#0d47a1,stroke-width:2px,color:#fff;
    classDef report fill:#7B1FA2,stroke:#4a148c,stroke-width:2px,color:#fff;
    classDef industry fill:#388E3C,stroke:#1b5e20,stroke-width:2px,color:#fff;
    classDef stock fill:#F57C00,stroke:#e65100,stroke-width:2px,color:#fff;
    classDef theme fill:#D32F2F,stroke:#b71c1c,stroke-width:2px,color:#fff;

    %% Markets
    M_TW["台股市場 (加權/OTC/期權)"]:::market
    M_US["美股市場 (四大指數/科技巨頭)"]:::market
    M_JP["日股市場 (日經225/東證)"]:::market
    M_HK["港陸市場 (恆生/上證/通膨)"]:::market
    M_ETF["ETF配置 (台美市值/反向/債券)"]:::market

    %% Key Reports
    R_TW_MORN["20261110 台股晨訊"]:::report
    R_TW_POST["20261109 台股盤後分析"]:::report
    R_TW_DT["20261110 台股當沖速報"]:::report
    R_TW_STR["20261110 十月交易結構"]:::report
    R_US_MORN["20261110 美股晨訊"]:::report
    R_JP_MORN["20261110 日股晨訊"]:::report
    R_HK_MORN["20261110 港股晨訊"]:::report
    R_MACRO["20261109 全球股債匯週報"]:::report
    R_CPI["20261109 中國10月CPI/PPI"]:::report
    R_OPT["20261109 光通訊焦點產業"]:::report
    R_CHEM["20261110 塑化報價利差週報"]:::report
    R_8081["20261110 致新8081研究報告"]:::report
    R_TOP5["20261110 今日五檔焦點股"]:::report
    R_ETF_TW["20261109 ETF交易追蹤"]:::report
    R_ETF_US["20261109 複委託ETF週報"]:::report

    %% Link Markets to Reports
    M_TW --> R_TW_MORN
    M_TW --> R_TW_POST
    M_TW --> R_TW_DT
    M_TW --> R_TW_STR
    M_TW --> R_TOP5
    M_US --> R_US_MORN
    M_US --> R_MACRO
    M_JP --> R_JP_MORN
    M_HK --> R_HK_MORN
    M_HK --> R_CPI
    M_ETF --> R_ETF_TW
    M_ETF --> R_ETF_US

    %% Industries & Stocks
    subgraph S_TECH["半導體 & AI 硬體"]
        ST_2330["台積電 (2330)"]:::stock
        ST_3661["世芯-KY (3661)"]:::stock
        ST_3693["營邦 (3693)"]:::stock
        ST_2454["聯發科 (2454)"]:::stock
        ST_1560["中砂 (1560)"]:::stock
        ST_8299["群聯 (8299)"]:::stock
        ST_8081["致新 (8081)"]:::stock
    end

    subgraph S_OPTICAL["光通訊 CPO 族群"]
        ST_2455["全新 (2455)"]:::stock
        ST_3081["聯亞 (3081)"]:::stock
        ST_3450["聯鈞 (3450)"]:::stock
        ST_6442["光聖 (6442)"]:::stock
    end

    subgraph S_CHEM["塑化與原物料"]
        ST_1301["台塑 (1301)"]:::stock
        ST_PVC["乙烯 / VCM / PP"]:::stock
    end

    %% Link Reports to Stocks
    R_TOP5 --> ST_3661
    R_TOP5 --> ST_3693
    R_TOP5 --> ST_2454
    R_TOP5 --> ST_1560
    R_TOP5 --> ST_8299
    R_8081 --> ST_8081
    R_OPT --> ST_2455
    R_OPT --> ST_3081
    R_OPT --> ST_3450
    R_CHEM --> ST_1301
    R_CHEM --> ST_PVC
    R_TW_MORN --> ST_2330
```

---

## 🔍 核心標的檢索與報告索引對照表

| 核心標的 / 代碼 | 產業板塊 | 關鍵分析觀點 | 關聯報告 Markdown 檔案 |
|---|---|---|---|
| **台積電 (2330)** | 晶圓代工 / 權值股 | 2奈米與3奈米先進製程擴產，引領台股強彈重登4萬點 | [20261110_玉山投顧_台股晨訊.md](markdown/20261110_玉山投顧_台股晨訊.md) |
| **世芯-KY (3661)** | ASIC / 矽智財 | 3nm AI 加速器放量，美系 CSP 客戶全年貢獻上看 10 億美元，支撐 2670 / 壓力 4500 | [20261110台股_投資快訊_今日五檔焦點股.md](markdown/20261110台股_投資快訊_今日五檔焦點股.md) |
| **營邦 (3693)** | AI 伺服器 / 機櫃整合 | AMD Helios AI 機櫃量產直供北美雲端巨頭，10月營收年增 231%，支撐 480 / 壓力 660 | [20261110台股_投資快訊_今日五檔焦點股.md](markdown/20261110台股_投資快訊_今日五檔焦點股.md) |
| **聯發科 (2454)** | 手機晶片 / AI ASIC | 2027年首款雲端 AI ASIC 放量挑戰 160 億美元，天璣 9600 Pro 2nm 擴產，支撐 3200 / 壓力 4200 | [20261110台股_投資快訊_今日五檔焦點股.md](markdown/20261110台股_投資快訊_今日五檔焦點股.md) |
| **中砂 (1560)** | 半導體耗材 / 晶圓再生 | 台積電 2nm 鑽石碟擴充至 10 萬顆，CoWoS/HBM 研磨新品出貨，支撐 640 / 壓力 900 | [20261110台股_投資快訊_今日五檔焦點股.md](markdown/20261110台股_投資快訊_今日五檔焦點股.md) |
| **群聯 (8299)** | 快閃記憶體控制 IC | 企業級 SSD 控制晶片進入量產，邊緣 AI 落地爆發，評價落入低檔，支撐 1400 / 壓力 1860 | [20261110台股_投資快訊_今日五檔焦點股.md](markdown/20261110台股_投資快訊_今日五檔焦點股.md) |
| **致新 (8081)** | 電源管理 IC (PMIC) | 同業競爭加劇，PC/NB 需求平穩，維持「中立」投資評等，目標價 270 元 | [20261110_玉山投顧_研究報告_8081致新_中立_維持.md](markdown/20261110_玉山投顧_研究報告_8081致新_中立_維持.md) |
| **全新 (2455)** | 光通訊 / 化合物磊晶 | 受惠 800G/1.6T 光收發模組放量，累計成長率 54.3% | [20261109_短線焦點產業_光通訊相關族群.md](markdown/20261109_短線焦點產業_光通訊相關族群.md) |
| **聯亞 (3081)** | 光通訊 / 雷射磊晶 | 矽光子 (SiPh) 與 CPO 關鍵供應商，營運步入高速成長期 | [20261109_短線焦點產業_光通訊相關族群.md](markdown/20261109_短線焦點產業_光通訊相關族群.md) |
| **台塑 (1301)** | 塑化龍頭 | 上游乙烯抗跌，下游 PP 利差顯著擴大，為利差改善之主要受惠者 | [20261110_玉山投顧_塑化產品報價與利差週報.md](markdown/20261110_玉山投顧_塑化產品報價與利差週報.md) |
| **0050 / 009816** | 台灣市值型 ETF | 隨大盤崩跌面臨停損潮，反彈後觀察權值股填息力道 | [20261109_玉山投顧_ETF交易追蹤.md](markdown/20261109_玉山投顧_ETF交易追蹤.md) |
| **SMH / SOXX** | 美國半導體 ETF | 上週重挫逾 11%，週初迎來費半狂飆 6.9% 報復性反彈 | [20261109_玉山投顧_複委託ETF週報.md](markdown/20261109_玉山投顧_複委託ETF週報.md) |

---

## 🎯 投資主題與宏觀戰略總結

1. **台股大盤強彈與籌碼修復**：國安基金進場訊息疊加限空令，加權指數強彈 1,960 點（漲幅 4.94%）收復 4 萬點大關至 41,661 點，年線確立強支撐。融資去化後浮額沉澱，當沖量占比達 24.84%、成交值占比逾 42%，市場交投維持高熱度。
2. **美股科技巨頭與費半領漲**：費城半導體大漲 6.9%、那斯達克上漲 2.7%，市場消化 AI 資本支出回報疑慮，硬體加速器與算力基礎設施仍為中長線主軸。
3. **大中華總經剪刀差**：中國 10 月 CPI 回落至 0.7%，PPI 擴大至 5.7%，差距達 5.0 個百分點，反映上游大宗商品與能源價格抗跌，但終端內需消費仍待政策振興提振。
"""

with open(os.path.join(base_dir, 'KNOWLEDGE_MAP.md'), 'w', encoding='utf-8') as f:
    f.write(km_content)

print('Generated KNOWLEDGE_MAP.md')
