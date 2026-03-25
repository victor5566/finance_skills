# Finance Skills — 專案說明文件

> 中文版 | [English](README.en.md)

---

# Finance Skills — 技能插件

## 這是什麼

一個 Claude Code 金融服務技能插件的 mono-repo。技能讓 Claude 學習金融領域知識，
協助回答金融問題、建立金融工具，並標記合規疑慮。完整架構與路線圖請參閱 `PLAN.md`。

## 目前狀態

共 81 個技能，分布於 7 個插件領域，存放於 `plugins/` 下：

- **core**（3 個技能）— 數學基礎（報酬率、貨幣時間價值、統計）
- **wealth-management**（31 個技能）— 投資知識、資產類別、投資組合建構、個人理財
- **compliance**（16 個技能）— 美國證券法規指引（FINRA、SEC、ERISA、FinCEN、CFA Institute GIPS）
- **advisory-practice**（10 個技能）— 顧問系統、客戶開戶、CRM、投資組合管理、提案、計費
- **trading-operations**（9 個技能）— 委託單生命週期、執行、交割、保證金、交易所連線、操作風險
- **client-operations**（8 個技能）— 帳戶開設、維護、轉帳、對帳、公司行動、STP
- **data-integration**（4 個技能）— 參考資料、市場資料、整合模式、資料品質

技能透過 `install.sh` 安裝至專案的 `.claude/skills/`。

## 使用技能

### 技能結構

每個技能是 `plugins/<plugin-name>/skills/` 下的一個目錄，包含 `SKILL.md`，
以及可選的 `scripts/` 子目錄（Python 參考實作）。SKILL.md 教授領域知識；scripts 提供可執行的計算。

### 模板

所有技能遵循 `PLAN.md` 中的模板，主要章節：

- **Purpose**（目的）— 技能的用途
- **When to Use**（使用時機）— 觸發詞與情境
- **Core Concepts**（核心概念）— 領域知識
- **Worked Examples**（實作範例）— 具體場景與分析
- **Common Pitfalls**（常見錯誤）— 應避免的錯誤
- **Cross-References**（交叉參考）— 相關技能連結

### 建立新技能

1. 確認 `PLAN.md` 中的技能列表與插件分配
2. 在 `plugins/<plugin-name>/skills/<skill-name>/` 下建立技能目錄
3. 嚴格遵循 SKILL.md 模板
4. 量化技能：包含關鍵公式與數值範例
5. 合規/操作技能：使用情境範例（情境 / 合規問題 / 分析），引用具體規則編號，省略公式與參考實作章節
6. 雙向新增相關技能的交叉參考
7. 完成後更新 `PLAN.md` 的實作狀態

### Python 腳本

僅量化技能（core、wealth-management）附 Python 腳本。腳本規範：

- 使用 Python 3.11+，僅限 numpy/scipy/pandas 相依套件
- 獨立可執行（不需安裝）
- 採用類別組織，使用靜態方法
- 包含完整 docstrings 與型別提示
- 公式須與對應 SKILL.md 一致

## 命名慣例

- 技能目錄：`小寫-連字號`（例：`fixed-income-sovereign`）
- Python 檔案：`小寫_底線`（例：`fixed_income_sovereign.py`）
- 技能內容不使用 emoji
- 合規技能須在行內引用具體規則編號與法案條文
- 交叉參考需包含層級/插件名稱及關係說明
- 不新增超出明確需求的功能、測試或工具

## Linear 議題追蹤

- **專案**：Finance Skills（團隊：Joellewis）
- commit 訊息與 PR 標題須引用議題 ID（例：JOE-42）
- 實作過程中發現的議題送至 Triage，標記 `agent-drafted`

---

# Finance Dashboard — 網頁應用程式

## 概覽

建立在技能 repo 之上的全端金融資料儀表板。
從 Yahoo Finance 抓取即時現金流資料，儲存至 MongoDB，
並透過深色主題的單頁應用程式呈現互動圖表。

**技術棧**：Python / Flask · MongoDB (localhost:27017) · yfinance · Chart.js 4

## 啟動方式

```bash
# 先確認 MongoDB 已啟動，再執行：
python app.py
# 開啟瀏覽器：http://localhost:5000
```

**一次性安裝相依套件：**

```bash
pip install flask pymongo yfinance
```

## 檔案結構

```
Finance_skill/
├── app.py                      # Flask 後端 + SPA HTML（單一檔案）
├── server.ps1                  # PowerShell 啟動/停止/狀態腳本（自動清除舊實例）
├── generate_cashflow_chart.py  # 獨立 CLI 圖表產生器（舊版 v1）
├── aapl_cashflow.html          # 靜態圖表輸出範例
└── .claude/skills/             # 已安裝的 84 個金融技能（JoelLewis）
```

## 啟動 Server

使用 `server.ps1` — 啟動前自動清除 port 5000 上的舊實例：

```powershell
.\server.ps1          # 啟動（自動清除舊實例）
.\server.ps1 stop     # 停止
.\server.ps1 status   # 顯示執行中的 PID
```

**請勿直接使用 `Start-Process`** — 會在同一 port 留下殭屍進程，導致 API 回應舊版程式碼。

## 股票目錄

307 個股票代號跨四個美國交易所類別，同時儲存於 `app.py`（CATALOG dict）與
MongoDB（`finance_dashboard.catalog` collection）。`/api/catalog` 端點從 MongoDB 讀取。
所有交易所分類已透過 yfinance 核實並修正；4 個下市/被收購股票（COUP、DFS、ABC、PARA）已移除。

| 交易所    | 數量 | 內容 |
|-----------|------|------|
| NasdaqGS  | 94   | NASDAQ Global Select Market — AAPL、MSFT、NVDA 等大型 NMS 掛牌股票 |
| NASDAQ    | 18   | NASDAQ Global/Capital Market — ETF（QQQ/TLT/BND/BOTZ/ICLN…）+ MDB、TTD、ENPH、PLUG |
| NYSE      | 141  | 藍籌股、金融（BLK/BX/KKR）、工業/國防（LMT/NOC）、能源（SLB/OXY）、醫療、零售 |
| AMEX      | 54   | ETF：槓桿型（SOXL/TECL/TQQQ）、主題型（BITO/GBTC/ARKK）、產業型（XLF/XLE/XLK） |

初始頁面顯示熱門股票：`AAPL  MSFT  NVDA  TSLA  AMZN`

## REST API

| 方法   | 路徑                                      | 說明                                               |
|--------|-------------------------------------------|----------------------------------------------------|
| GET    | `/`                                       | SPA 儀表板 HTML                                    |
| GET    | `/api/catalog?exchange=&q=`               | 從 MongoDB 篩選目錄（支援 regex 搜尋）             |
| GET    | `/api/stocks`                             | 列出 MongoDB 中所有股票（僅摘要欄位）              |
| POST   | `/api/stocks`                             | 新增股票 — body: `{"ticker":"TSLA"}`               |
| GET    | `/api/stocks/<ticker>`                    | 完整資料，含年度 + 季度序列                        |
| DELETE | `/api/stocks/<ticker>`                    | 從 MongoDB 刪除股票                                |
| POST   | `/api/stocks/<ticker>/refresh`            | 重新從 Yahoo Finance 抓取所有資料                  |
| GET    | `/api/popular`                            | 載入熱門 5 檔（若不在 DB 中則自動抓取）           |
| GET    | `/api/stocks/<ticker>/history?period=1y`  | 股價歷史（用於趨勢圖，詳見下方）                   |
| GET    | `/api/compare?tickers=&period=1y`         | 多股正規化漲跌幅（用於比較圖）                     |

### History 端點參數

`period` 可選值：`1d` `1mo` `3mo` `6mo` `1y`（預設）`2y` `5y`

回應欄位：

- `dates[]` — 1d 時為 `HH:MM`；其他期間為 `YYYY-MM-DD`
- `close[]` — 收盤價（1d 為 5 分鐘 K，≤1y 為日線，2y/5y 為週線）
- `volume[]` — 成交量
- `ma20[]` — 1d 時為 MA5；其他期間為 MA20（前 N-1 個點為 null）
- `ma50[]` — 1d 時為 MA20；其他期間為 MA50
- `ma_labels[]` — 1d 時為 `["MA5","MA20"]`；其他為 `["MA20","MA50"]`
- `stats` — `latest_price`、`pct_change`、`high_52w`、`low_52w`、`pe_ratio`（優先讀 MongoDB，無資料才呼叫 yfinance）

Interval 自動選擇：`5m`（1d）· `1d`（1mo–1y）· `1wk`（2y/5y）

## MongoDB Schema

資料庫 `finance_dashboard`，collections：`stocks` 與 `catalog`

```json
{
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "exchange": "NASDAQ",
  "sector": "Technology",
  "current_price": 213.49,
  "market_cap": 3200000000000,
  "annual":    { "labels": ["FY2021",...], "ocf": [...], "capex": [...], "fcf": [...], "interest": [...] },
  "quarterly": { "labels": ["Q1'24",...],  "ocf": [...], "capex": [...], "fcf": [...], "interest": [...] },
  "has_quarterly": true,
  "kpis": { "latest_ocf": 111482, "latest_fcf": 98767, "ocf_cagr": 1.7, "fcf_conversion": 88.6, "pe_ratio": 31.8 },
  "last_updated": "2026-03-24T12:00:00Z"
}
```

所有金額以**百萬美元（$M）**儲存。ETF 無現金流資料，`annual` 欄位為 `null`。

`catalog` collection schema：`{ ticker, name, exchange }` — 索引：`ticker`（唯一）與 `exchange`。

## 前端功能

### 導覽列

- **固定標題列** — 即時搜尋（220ms 防抖），下拉自動完成（最多 12 筆）
- **交易所分頁** — ALL / NasdaqGS / NASDAQ / NYSE / AMEX — 同時過濾股票卡片與目錄瀏覽器
- **瀏覽目錄** — 切換顯示所選交易所的所有股票格狀列表；已加入的顯示「已加入」徽章

### 儀表板區塊

- **熱門股票** — 頁面開啟時自動載入 AAPL / MSFT / NVDA / TSLA / AMZN（若尚未快取則從 Yahoo Finance 抓取）
- **我的股票** — 使用者自行新增的股票（不含熱門 5 檔），依交易所過濾，持久化至 MongoDB
- **股票卡片** — 顯示：代號、名稱、交易所徽章、現價、市值、OCF / FCF / CAGR / FCF 轉換率 / **P/E 本益比** KPI、最後更新時間、刷新與刪除操作

### 圖表面板（點擊任意卡片開啟）

共三個頁籤，顯示規則：
- 有現金流資料 → 顯示三個頁籤，預設開啟**現金流分析**
- 無現金流資料（ETF）→ 現金流分析頁籤隱藏，直接開啟**價格趨勢**

#### 頁籤一 — 現金流分析

- **Chart.js** 長條圖 + 折線圖混合圖表：
  - 綠色長條 — 營業現金流（OCF）
  - 紅色長條 — 資本支出（CapEx）
  - 橘色長條 — 利息費用
  - 藍色填充折線 — 自由現金流（FCF）
- **期間切換**（年度 / 季度）— 僅在 `has_quarterly: true` 時顯示；ETF 與資料不足的股票隱藏
- **KPI 卡片** — 最新 OCF、FCF、OCF CAGR、FCF 轉換率
- **資料表格** — 完整歷史，YoY% 以綠/紅標色，含 FCF 轉換率欄位

#### 頁籤二 — 價格趨勢

- **統計列** — 目前價格、區間漲跌幅（綠/紅）、區間最高、區間最低、P/E 本益比（從 MongoDB `kpis.pe_ratio` 讀取；未儲存時才即時抓取）
- **時間區間按鈕** — **1D** / 1M / 3M / 6M / **1Y**（預設）/ 2Y / 5Y
  - 1D：5 分鐘 K 線，X 軸顯示 HH:MM，MA 切換為 MA5/MA20
  - 1M–1Y：日線，MA20/MA50
  - 2Y–5Y：週線，MA20/MA50
- **價格圖** — 藍色收盤價折線（漸層填充）+ MA（黃色虛線）+ MA（紅色虛線）；圖例動態更新
- **成交量圖** — 價格圖下方獨立長條圖；上漲日綠色，下跌日紅色
- 資料在切換頁籤 / 更改區間時即時從 Yahoo Finance 抓取（不儲存至 MongoDB）

#### 頁籤三 — 多股比較

- 切換至此頁籤時自動帶入目前股票；最多可加入 8 檔
- **股票輸入框** — 輸入代碼或公司名稱，自動完成下拉（最多 10 筆，含交易所徽章，與標題列搜尋體驗一致）；點擊或按 Enter 加入
- **顏色徽章** — 每檔股票對應不同顏色，點擊 ✕ 可移除
- **時間區間按鈕** — 1D / 1M / 3M / 6M / 1Y（預設）/ 2Y / 5Y
- **比較折線圖** — Y 軸顯示相對起始日的漲跌幅（%），不同價位股票可直接比較；Tooltip 同時顯示 % 漲跌與當日實際價格
- 資料即時從 `/api/compare` 抓取，不儲存至 MongoDB

## kezsmeister/claude-finance-skills（斜線指令）

安裝於 `~/.claude/skills/`，可在 Claude Code 中直接使用：

```
/annual-revenue  <ticker>      10 年年度營收 + YoY 成長表
/quarterly-revenue <ticker>    季度營收表
/annual-eps  <ticker>          年度稀釋 EPS
/quarterly-eps <ticker>        季度 EPS
/annual-dividend <ticker>      年度每股股息
/quarterly-dividend <ticker>   季度股息
/annual-capex <ticker>         年度資本支出
/annual-wads <ticker>          加權平均稀釋股數
/cashflow-chart <ticker>       互動式 HTML 現金流圖表（在 Chrome 開啟）
```

這些技能需要開啟遠端除錯的 Chrome：

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="C:\Users\victo\AppData\Local\chrome-debug-profile"
```

MCP 伺服器（`chrome-devtools` + `yahoo-finance`）已預先設定於 `~/.claude/settings.json`。
首次設定後需重新啟動 Claude Code 才能生效。

## Schema 遷移

`app.py` v1 將現金流資料以平坦欄位儲存（`years`、`ocf`、`capex`、`fcf`、`interest` 於頂層）。
v2 改為巢狀結構（`annual.labels`、`annual.ocf`…）。

`get_stock()` 中的 `migrate_old_schema()` 在首次讀取時自動偵測 v1 文件，
就地轉換並寫回 MongoDB — 無需手動遷移。

## 已知限制

- yfinance 預設僅回傳約 4–5 年的現金流資料（Yahoo Finance 免費版限制）
- ETF 無現金流資料 — 以 `annual: null` 儲存；前端自動開啟價格趨勢頁籤
- 股價歷史（趨勢頁籤）即時抓取，不快取至 MongoDB
- 1D 盤中資料僅在開盤期間或收盤後可用（yfinance 限制）
- 部分股票 P/E 可能為 `null`（yfinance `fast_info` 限制）
- Flask 啟動前須先確認 MongoDB 在本地執行
- 避免快速批量抓取多檔股票（Yahoo Finance 頻率限制）

## 版本紀錄

| 版本 | 日期       | 變更內容 |
|------|------------|---------|
| v1   | 2026-03-24 | 初始 Flask 應用 — 單一 AAPL 圖表，平坦 MongoDB schema |
| v2   | 2026-03-24 | 多股票儀表板、NYSE/NASDAQ/AMEX 目錄（312 檔），交易所分頁、搜尋下拉、目錄瀏覽、年度/季度切換、熱門股票區塊 |
| v2.1 | 2026-03-24 | 新增 `migrate_old_schema` 遷移工具；修正 MSFT/AAPL/TSLA v1 資料無法顯示的問題 |
| v2.2 | 2026-03-24 | 價格趨勢頁籤：收盤價折線、MA20/MA50、成交量長條、時間區間選擇器（1M–5Y）、統計列 |
| v2.3 | 2026-03-24 | ETF 支援：無現金流股票以 `annual: null` 儲存，CF 頁籤隱藏，自動開啟趨勢；修正 BOTZ 交易所（AMEX→NASDAQ）；核實全部 311 檔股票交易所分類，修正 41 筆錯誤，移除 4 個下市股票（COUP/DFS/ABC/PARA），目錄縮減為 307 檔並存入 MongoDB `catalog` collection；`server.ps1` 可靠啟動管理；新增 1D 時間區間（5 分鐘 K、HH:MM 標籤、MA5/MA20） |
| v2.4 | 2026-03-24 | 新增 NasdaqGS 交易所類別（94 個 NMS 股票從 NASDAQ 分離）；P/E 存入 `kpis.pe_ratio`（使用 `trailingPE`/`forwardPE`），顯示於股票卡片，舊資料首次開啟時自動補抓；趨勢頁 P/E 改從 MongoDB 讀取，不再依賴不穩定的 `fast_info` |
| v2.5 | 2026-03-25 | 多股比較疊加圖：`/api/compare` 端點（正規化漲跌幅），新增「多股比較」頁籤，顏色徽章 + ✕ 移除，輸入框自動完成下拉（與標題列搜尋體驗一致），最多 8 檔，區間 1D–5Y |
| v2.6 | 2026-03-25 | 股票篩選器面板：`/api/screener`（全目錄合併 — 307 檔，KPI 條件透過 MongoDB `$gte`/`$lte` 篩選）、`/api/sectors` 端點、OCF CAGR / FCF 轉換率 / P/E / 產業 / 交易所篩選輸入，分頁列「篩選器」切換按鈕，未載入股票顯示 `—` KPI 並提供逐列「載入」按鈕 |
| v2.7 | 2026-03-25 | 批量資料載入器：`/api/bulk-fetch` SSE 端點即時串流逐檔進度；篩選器面板內「載入全部數據」按鈕 + 進度條；已載入的股票自動跳過；完成後自動刷新篩選器與我的股票 |
| v2.8 | 2026-03-25 | 股息歷史圖表：`/api/stocks/<ticker>/dividends` 端點（yfinance `t.dividends`）；新增「股息歷史」頁籤；年度長條圖（黃色）；KPI 統計列（年度股息/股、殖利率%、最近一次股息）；付息日期資料表含年度 YoY%；不配息股票顯示提示訊息 |
| v2.9 | 2026-03-25 | 修正殖利率顯示（yfinance 已回傳 %，移除多餘 ×100）；「我的股票」標題新增「全部清除」按鈕（只清除 pinned 非熱門股票）；股票文件新增 `pinned` 欄位 — 批量載入用 `$setOnInsert` 設 `pinned:false`，手動加入設 `pinned:true`；`GET /api/stocks` 過濾 `pinned != false`；新增 `/api/stocks/<ticker>/pin` 端點；篩選器點選已批量載入的股票改為直接 pin，不重新抓取資料 |
| v2.10 | 2026-03-25 | 營收/EPS 圖表頁籤：`/api/stocks/<ticker>/financials` 端點（yfinance `t.income_stmt` + `t.quarterly_income_stmt`）；新增「營收/EPS」頁籤；雙軸 Chart.js 組合圖（總營收藍色長條＋淨利綠色長條對應左軸，稀釋 EPS 橘色折線對應右軸）；年度/季度切換；KPI 統計列（最新年度營收、營收 CAGR、最新淨利、稀釋 EPS）；資料表含 YoY% 色碼標示；ETF 顯示「無財務報表資料」提示 |

## 未來改善方向

- [x] 多股票比較疊加圖
- [x] 股票篩選器（依 CAGR、FCF 轉換率、產業篩選）
- [x] 股息歷史圖表
- [x] 營收 / EPS 圖表頁籤
- [ ] 匯出 CSV / Excel
- [ ] Docker Compose 設定（Flask + MongoDB 一鍵啟動）
- [ ] WebSocket 即時股價推播
