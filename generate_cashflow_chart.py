"""
Cash Flow Chart Generator
依照 cashflow-chart skill 規格，用 yfinance 抓取資料並產生互動式 HTML 圖表
"""

import yfinance as yf
import json
import sys
import os
import math

def format_value(val, in_millions=True):
    """Format value for display (input in millions)"""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return "N/A"
    if in_millions:
        if abs(val) >= 1000:
            return f"${val/1000:.2f}B"
        return f"${val:.0f}M"
    return f"${val:.2f}"

def get_cashflow_data(ticker_symbol):
    """Fetch cash flow and income statement data from Yahoo Finance"""
    ticker = yf.Ticker(ticker_symbol)

    # Get cash flow statement (annual)
    cf = ticker.cashflow
    income = ticker.income_stmt
    info = ticker.info

    company_name = info.get("longName", ticker_symbol)

    data = {}

    # Operating Cash Flow
    ocf_key = None
    for k in cf.index:
        if "Operating" in k and "Cash" in k:
            ocf_key = k
            break
    if ocf_key is None:
        for k in cf.index:
            if "cash" in k.lower() and "operat" in k.lower():
                ocf_key = k
                break

    # Capital Expenditure
    capex_key = None
    for k in cf.index:
        if "Capital" in k and "Expenditure" in k:
            capex_key = k
            break
    if capex_key is None:
        for k in cf.index:
            if "capex" in k.lower() or ("capital" in k.lower() and "expend" in k.lower()):
                capex_key = k
                break

    # Free Cash Flow
    fcf_key = None
    for k in cf.index:
        if "Free" in k and "Cash" in k:
            fcf_key = k
            break

    # Interest Expense
    int_key = None
    for k in income.index:
        if "Interest" in k and "Expense" in k:
            int_key = k
            break
    if int_key is None:
        for k in income.index:
            if "interest" in k.lower() and "expens" in k.lower():
                int_key = k
                break

    years = []
    ocf_vals = []
    capex_vals = []
    fcf_vals = []
    int_vals = []

    # Use cashflow columns (dates)
    for col in reversed(cf.columns):
        year = col.year
        years.append(f"FY{year}")

        # OCF in millions
        ocf = cf.loc[ocf_key, col] / 1e6 if ocf_key and ocf_key in cf.index else None
        ocf_vals.append(round(ocf, 1) if ocf is not None and not math.isnan(ocf) else None)

        # CapEx - use absolute value
        capex = cf.loc[capex_key, col] / 1e6 if capex_key and capex_key in cf.index else None
        if capex is not None and not math.isnan(capex):
            capex_vals.append(round(abs(capex), 1))
        else:
            capex_vals.append(None)

        # FCF - compute if not available
        if fcf_key and fcf_key in cf.index:
            fcf = cf.loc[fcf_key, col] / 1e6
            fcf_vals.append(round(fcf, 1) if not math.isnan(fcf) else None)
        elif ocf_vals[-1] is not None and capex_vals[-1] is not None:
            fcf_vals.append(round(ocf_vals[-1] - capex_vals[-1], 1))
        else:
            fcf_vals.append(None)

        # Interest Expense
        if int_key and int_key in income.index and col in income.columns:
            ie = income.loc[int_key, col] / 1e6
            int_vals.append(round(abs(ie), 1) if not math.isnan(ie) else None)
        else:
            int_vals.append(None)

    return {
        "ticker": ticker_symbol.upper(),
        "name": company_name,
        "years": years,
        "ocf": ocf_vals,
        "capex": capex_vals,
        "fcf": fcf_vals,
        "interest": int_vals,
    }


def compute_kpis(data):
    ocf = [v for v in data["ocf"] if v is not None]
    fcf = [v for v in data["fcf"] if v is not None]

    first_ocf = ocf[0] if ocf else None
    latest_ocf = ocf[-1] if ocf else None
    latest_fcf = fcf[-1] if fcf else None

    cagr = None
    if first_ocf and latest_ocf and first_ocf > 0 and len(ocf) > 1:
        n = len(ocf) - 1
        cagr = ((latest_ocf / first_ocf) ** (1 / n) - 1) * 100

    fcf_conversion = None
    if latest_ocf and latest_fcf and latest_ocf != 0:
        fcf_conversion = (latest_fcf / latest_ocf) * 100

    growth = None
    if first_ocf and latest_ocf and first_ocf > 0:
        growth = ((latest_ocf / first_ocf) - 1) * 100

    return {
        "first_ocf": first_ocf,
        "latest_ocf": latest_ocf,
        "latest_fcf": latest_fcf,
        "cagr": cagr,
        "fcf_conversion": fcf_conversion,
        "growth": growth,
    }


def build_table_rows(data):
    rows = []
    years = data["years"]
    ocf = data["ocf"]
    capex = data["capex"]
    fcf = data["fcf"]
    interest = data["interest"]

    for i in range(len(years)):
        yoy = ""
        if i > 0 and ocf[i] is not None and ocf[i-1] is not None and ocf[i-1] != 0:
            pct = ((ocf[i] - ocf[i-1]) / abs(ocf[i-1])) * 100
            sign = "+" if pct >= 0 else ""
            color = "#4ade80" if pct >= 0 else "#f87171"
            yoy = f'<span style="color:{color}">{sign}{pct:.1f}%</span>'

        rows.append({
            "year": years[i],
            "ocf": format_value(ocf[i]),
            "yoy": yoy or "–",
            "capex": format_value(capex[i]),
            "interest": format_value(interest[i]),
            "fcf": format_value(fcf[i]),
            "fcf_conv": f"{(fcf[i]/ocf[i]*100):.0f}%" if fcf[i] and ocf[i] else "N/A",
        })
    return rows


def generate_html(data, kpis, table_rows):
    ticker = data["ticker"]
    name = data["name"]

    # Convert None to null for JS
    def to_js(arr):
        return json.dumps([v for v in arr])

    table_html = ""
    for r in table_rows:
        table_html += f"""
        <tr>
            <td>{r['year']}</td>
            <td style="color:#4ade80">{r['ocf']}</td>
            <td>{r['yoy']}</td>
            <td style="color:#f87171">{r['capex']}</td>
            <td style="color:#fbbf24">{r['interest']}</td>
            <td style="color:#60a5fa">{r['fcf']}</td>
            <td style="color:#60a5fa">{r['fcf_conv']}</td>
        </tr>"""

    cagr_str = f"{kpis['cagr']:.1f}%" if kpis['cagr'] is not None else "N/A"
    growth_str = f"{kpis['growth']:.0f}%" if kpis['growth'] is not None else "N/A"
    conv_str = f"{kpis['fcf_conversion']:.0f}%" if kpis['fcf_conversion'] is not None else "N/A"

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{ticker} — Cash Flow Chart</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #1a1a2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', system-ui, sans-serif;
    padding: 24px;
  }}
  h1 {{ font-size: 1.6rem; margin-bottom: 4px; color: #e2e8f0; }}
  .subtitle {{ color: #94a3b8; margin-bottom: 20px; font-size: 0.9rem; }}
  .chart-wrapper {{
    background: #16213e;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
    height: 520px;
    position: relative;
  }}
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
  }}
  .kpi-card {{
    background: #16213e;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
  }}
  .kpi-value {{ font-size: 1.4rem; font-weight: 700; margin-bottom: 4px; }}
  .kpi-label {{ font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }}
  .kpi-sub {{ font-size: 0.75rem; color: #64748b; margin-top: 2px; }}
  table {{
    width: 100%;
    border-collapse: collapse;
    background: #16213e;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 24px;
  }}
  th {{
    background: #0f3460;
    padding: 10px 12px;
    text-align: left;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94a3b8;
  }}
  td {{
    padding: 9px 12px;
    border-bottom: 1px solid #1e293b;
    font-size: 0.85rem;
  }}
  tr:hover td {{ background: #1e293b; }}
  .observations {{
    background: #16213e;
    border-radius: 10px;
    padding: 20px;
  }}
  .observations h3 {{ margin-bottom: 12px; color: #e2e8f0; font-size: 1rem; }}
  .observations ul {{ padding-left: 20px; }}
  .observations li {{ margin-bottom: 8px; color: #94a3b8; font-size: 0.85rem; line-height: 1.5; }}
  .source {{ margin-top: 16px; font-size: 0.75rem; color: #475569; }}
</style>
</head>
<body>
<h1>{name} ({ticker})</h1>
<p class="subtitle">Cash Flow Analysis — 資料來源: Yahoo Finance | 數值單位: 百萬美元 (M)</p>

<div class="chart-wrapper">
  <canvas id="cfChart"></canvas>
</div>

<div class="kpi-grid">
  <div class="kpi-card">
    <div class="kpi-value" style="color:#4ade80">{format_value(kpis['first_ocf'])}</div>
    <div class="kpi-label">最早年度 OCF</div>
    <div class="kpi-sub">起始基準</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value" style="color:#4ade80">{format_value(kpis['latest_ocf'])}</div>
    <div class="kpi-label">最新年度 OCF</div>
    <div class="kpi-sub">成長 {growth_str}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value" style="color:#fbbf24">{cagr_str}</div>
    <div class="kpi-label">OCF CAGR</div>
    <div class="kpi-sub">年複合成長率</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value" style="color:#60a5fa">{format_value(kpis['latest_fcf'])}</div>
    <div class="kpi-label">最新年度 FCF</div>
    <div class="kpi-sub">自由現金流</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value" style="color:#60a5fa">{conv_str}</div>
    <div class="kpi-label">FCF 轉換率</div>
    <div class="kpi-sub">FCF / OCF</div>
  </div>
</div>

<table>
  <thead>
    <tr>
      <th>財年</th>
      <th style="color:#4ade80">營業現金流</th>
      <th>YoY%</th>
      <th style="color:#f87171">資本支出</th>
      <th style="color:#fbbf24">利息費用</th>
      <th style="color:#60a5fa">自由現金流</th>
      <th style="color:#60a5fa">FCF轉換率</th>
    </tr>
  </thead>
  <tbody>
    {table_html}
  </tbody>
</table>

<div class="observations">
  <h3>📊 關鍵觀察</h3>
  <ul id="obs-list">
    <li>OCF CAGR 為 <strong style="color:#fbbf24">{cagr_str}</strong>，顯示長期現金流生成能力。</li>
    <li>最新年度自由現金流 <strong style="color:#60a5fa">{format_value(kpis['latest_fcf'])}</strong>，FCF 轉換率 {conv_str}。</li>
    <li>資本支出（紅色）反映公司資本密集程度，越低表示越輕資產模式。</li>
    <li>利息費用（橘色）反映公司槓桿水準，持續上升需留意財務壓力。</li>
    <li>資料來源：Yahoo Finance，僅供教育與研究參考，不構成投資建議。</li>
  </ul>
  <p class="source">⚠️ 免責聲明：本圖表數據來自 Yahoo Finance，僅供參考，不構成投資建議。</p>
</div>

<script>
ChartDataLabels && Chart.register(ChartDataLabels);

const labels = {to_js(data['years'])};
const ocf    = {to_js(data['ocf'])};
const capex  = {to_js(data['capex'])};
const fcf    = {to_js(data['fcf'])};
const intExp = {to_js(data['interest'])};

const ctx = document.getElementById('cfChart').getContext('2d');

new Chart(ctx, {{
  type: 'bar',
  data: {{
    labels,
    datasets: [
      {{
        label: '營業現金流 (OCF)',
        data: ocf,
        backgroundColor: 'rgba(74,222,128,0.75)',
        borderColor: 'rgba(74,222,128,1)',
        borderWidth: 1,
        borderRadius: 3,
        yAxisID: 'y',
      }},
      {{
        label: '資本支出 (CapEx)',
        data: capex,
        backgroundColor: 'rgba(248,113,113,0.75)',
        borderColor: 'rgba(248,113,113,1)',
        borderWidth: 1,
        borderRadius: 3,
        yAxisID: 'y',
      }},
      {{
        label: '利息費用',
        data: intExp,
        backgroundColor: 'rgba(251,191,36,0.75)',
        borderColor: 'rgba(251,191,36,1)',
        borderWidth: 1,
        borderRadius: 3,
        yAxisID: 'y',
      }},
      {{
        label: '自由現金流 (FCF)',
        data: fcf,
        type: 'line',
        borderColor: 'rgba(96,165,250,1)',
        backgroundColor: 'rgba(96,165,250,0.15)',
        borderWidth: 2.5,
        pointRadius: 4,
        pointHoverRadius: 6,
        fill: true,
        tension: 0.3,
        yAxisID: 'y',
        datalabels: {{ display: false }},
      }},
    ],
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{
      legend: {{
        position: 'bottom',
        labels: {{ color: '#cdd6f4', usePointStyle: true, padding: 20 }},
      }},
      tooltip: {{
        backgroundColor: '#0f3460',
        titleColor: '#e2e8f0',
        bodyColor: '#94a3b8',
        callbacks: {{
          label: ctx => {{
            const v = ctx.parsed.y;
            if (v === null) return `${{ctx.dataset.label}}: N/A`;
            const abs = Math.abs(v);
            const fmt = abs >= 1000 ? `${{(v/1000).toFixed(2)}}B` : `${{v.toFixed(0)}}M`;
            return ` ${{ctx.dataset.label}}: ${{fmt}}`;
          }}
        }}
      }},
      datalabels: {{
        display: (ctx) => ctx.datasetIndex === 0 && ctx.dataIndex % 2 === 0,
        color: '#4ade80',
        anchor: 'end',
        align: 'top',
        font: {{ size: 10, weight: 'bold' }},
        formatter: v => {{
          if (!v) return '';
          return Math.abs(v) >= 1000 ? `${{(v/1000).toFixed(1)}}B` : `${{v.toFixed(0)}}M`;
        }},
      }},
    }},
    scales: {{
      x: {{
        ticks: {{ color: '#94a3b8', font: {{ size: 11 }} }},
        grid: {{ color: 'rgba(255,255,255,0.04)' }},
      }},
      y: {{
        ticks: {{
          color: '#94a3b8',
          font: {{ size: 11 }},
          callback: v => Math.abs(v) >= 1000 ? `$${{(v/1000).toFixed(0)}}B` : `$${{v}}M`,
        }},
        grid: {{ color: 'rgba(255,255,255,0.06)' }},
      }},
    }},
  }},
}});
</script>
</body>
</html>
"""


def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    print(f"正在抓取 {ticker} 的現金流資料...")

    data = get_cashflow_data(ticker)
    print(f"  公司名稱: {data['name']}")
    print(f"  年份數量: {len(data['years'])} 年")

    kpis = compute_kpis(data)
    table_rows = build_table_rows(data)
    html = generate_html(data, kpis, table_rows)

    out_path = os.path.join(os.path.dirname(__file__), f"{ticker.lower()}_cashflow.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  HTML 已儲存: {out_path}")
    return out_path


if __name__ == "__main__":
    path = main()
    print(f"\n完成！檔案路徑: {path}")
