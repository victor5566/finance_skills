# Finance Skills — Project Instructions

## What This Is

A mono-repo of Claude Code skill plugins for financial services. Skills teach Claude
domain knowledge so it can assist with finance questions, build financial tools, and
flag compliance concerns. See `PLAN.md` for the full architecture and roadmap.

## Current State

81 skills across 7 plugin domains, organized under `plugins/`:
- **core** (3 skills) — math foundations (returns, TVM, statistics)
- **wealth-management** (31 skills) — investment knowledge, asset classes, portfolio construction, personal finance
- **compliance** (16 skills) — US securities regulatory guidance (FINRA, SEC, ERISA, FinCEN, CFA Institute GIPS)
- **advisory-practice** (10 skills) — advisor-facing systems, onboarding, CRM, portfolio management, proposals, billing
- **trading-operations** (9 skills) — order lifecycle, execution, settlement, margin, exchange connectivity, operational risk
- **client-operations** (8 skills) — account opening, maintenance, transfers, reconciliation, corporate actions, STP
- **data-integration** (4 skills) — reference data, market data, integration patterns, data quality

Skills are installed into a project's `.claude/skills/` via `install.sh`.

## Working With Skills

### Skill Structure
Each skill is a directory in `plugins/<plugin-name>/skills/` containing a `SKILL.md`
and optionally a `scripts/` subdirectory with Python reference implementations. The
SKILL.md teaches domain knowledge; scripts provide runnable computation.

### Template
All skills follow the template documented in `PLAN.md`. Key sections:
- **Purpose** — what the skill enables
- **When to Use** — trigger phrases and situations
- **Core Concepts** — the domain knowledge
- **Worked Examples** — concrete scenarios with analysis
- **Common Pitfalls** — mistakes to avoid
- **Cross-References** — links to related skills

### Creating New Skills
1. Check `PLAN.md` for the planned skill list and plugin assignment
2. Create the skill directory under `plugins/<plugin-name>/skills/<skill-name>/`
3. Follow the SKILL.md template exactly
3. For quantitative skills: include Key Formulas and worked numerical examples
4. For compliance/operations skills: use scenario-based examples (Scenario / Compliance Issues / Analysis), cite specific rule numbers, omit Key Formulas and Reference Implementation sections
5. Add cross-references to related skills in both directions
6. Update `PLAN.md` implementation status when complete

### Python Scripts
Only quantitative skills (core, wealth-management) get Python scripts. Scripts should:
- Use Python 3.11+ with only numpy/scipy/pandas dependencies
- Be standalone (runnable without installation)
- Use class-based organization with static methods
- Include comprehensive docstrings and type hints
- Match the formulas documented in the corresponding SKILL.md

## Conventions

- Skill directories: `lowercase-hyphenated` (e.g., `fixed-income-sovereign`)
- Python files: `lowercase_underscore` (e.g., `fixed_income_sovereign.py`)
- No emojis in skill content
- Compliance skills cite specific rule numbers and act sections inline
- Cross-references include the layer/plugin and a brief description of the relationship
- Do not add features, tests, or tooling beyond what is explicitly requested

## Linear

- **Project**: Finance Skills (team: Joellewis)
- Reference issue IDs (e.g., JOE-42) in commit messages and PR titles
- Issues discovered during implementation go to Triage with `agent-drafted` label

---

# Finance Dashboard — Web Application

## Overview

A full-stack financial data dashboard built on top of this skills repo.
Fetches real-time cash flow data from Yahoo Finance, stores it in MongoDB,
and renders interactive charts through a dark-themed single-page web app.

**Stack**: Python / Flask · MongoDB (localhost:27017) · yfinance · Chart.js 4

## How to Run

**Option A — Docker Compose (recommended, no local installs needed):**
```bash
docker compose up --build
# Open: http://localhost:5000
# Stop: docker compose down
# Wipe data: docker compose down -v
```

**Option B — local Python:**
```bash
# MongoDB must be running first, then:
python app.py
# Open: http://localhost:5000
```

**Install dependencies once (Option B only):**
```bash
pip install -r requirements.txt
```

## File Structure

```
Finance_skill/
├── app.py                      # Flask backend + SPA HTML (all-in-one)
├── requirements.txt            # Python dependencies (flask, pymongo, yfinance)
├── Dockerfile                  # Flask app container image
├── docker-compose.yml          # Flask + MongoDB one-command setup
├── .dockerignore               # Files excluded from Docker build context
├── server.ps1                  # PowerShell start/stop/status script (kills old instances first)
├── generate_cashflow_chart.py  # Standalone CLI chart generator (legacy v1)
├── aapl_cashflow.html          # Example static chart output
└── .claude/skills/             # 84 installed finance skills (JoelLewis)
```

## How to Start the Server

Use `server.ps1` — always kills any existing instance on port 5000 before starting:

```powershell
.\server.ps1          # start (kills old instance automatically)
.\server.ps1 stop     # stop
.\server.ps1 status   # show running PID
```

Do NOT use `Start-Process` directly — it leaves orphaned instances on the same port.

## Stock Catalog

307 tickers across four US exchange categories, stored in both `app.py` (CATALOG dict) and
MongoDB (`finance_dashboard.catalog` collection). The `/api/catalog` endpoint reads
from MongoDB. Exchange assignments were verified against yfinance and corrected;
4 delisted/acquired tickers (COUP, DFS, ABC, PARA) were removed.

| Exchange  | Count | Content |
|-----------|-------|---------|
| NasdaqGS  | 94    | NASDAQ Global Select Market — AAPL, MSFT, NVDA and all major NMS-listed equities |
| NASDAQ    | 18    | NASDAQ Global/Capital Market — ETFs (QQQ/TLT/BND/BOTZ/ICLN…) + MDB, TTD, ENPH, PLUG |
| NYSE      | 141   | Blue chips, financials (BLK/BX/KKR), industrials/defence (LMT/NOC), energy (SLB/OXY), healthcare, retail |
| AMEX      | 54    | ETFs: leveraged (SOXL/TECL/TQQQ), thematic (BITO/GBTC/ARKK), sector (XLF/XLE/XLK) |

Popular tickers shown on initial load: `AAPL  MSFT  NVDA  TSLA  AMZN`

## REST API

| Method   | Path                                      | Description                                        |
|----------|-------------------------------------------|----------------------------------------------------|
| GET      | `/`                                       | SPA dashboard HTML                                 |
| GET      | `/api/catalog?exchange=&q=`               | Filter catalog from MongoDB (regex search)         |
| GET      | `/api/stocks`                             | List all stocks in MongoDB (summary fields only)   |
| POST     | `/api/stocks`                             | Add stock — body: `{"ticker":"TSLA"}`              |
| GET      | `/api/stocks/<ticker>`                    | Full data incl. annual + quarterly series          |
| DELETE   | `/api/stocks/<ticker>`                    | Remove stock from MongoDB                          |
| POST     | `/api/stocks/<ticker>/refresh`            | Re-fetch all data from Yahoo Finance               |
| GET      | `/api/popular`                            | Load popular 5 (auto-fetch if not in DB)           |
| GET      | `/api/stocks/<ticker>/history?period=1y`  | Price history for trend chart (see below)          |
| GET      | `/api/compare?tickers=&period=1y`         | Normalized % change for multi-ticker comparison    |

### History endpoint parameters

`period` values: `1d` `1mo` `3mo` `6mo` `1y` (default) `2y` `5y`

Response includes:
- `dates[]` — `HH:MM` for 1d period; `YYYY-MM-DD` for all others
- `close[]` — closing prices (5-min bars for 1d, daily for ≤1y, weekly for 2y/5y)
- `volume[]` — trading volume
- `ma20[]` — MA5 for 1d period; MA20 otherwise (null for first N-1 points)
- `ma50[]` — MA20 for 1d period; MA50 otherwise
- `ma_labels[]` — `["MA5","MA20"]` for 1d; `["MA20","MA50"]` otherwise
- `stats` — `latest_price`, `pct_change`, `high_52w`, `low_52w`, `pe_ratio` (reads from MongoDB first, falls back to yfinance)

Interval auto-selected: `5m` for 1d · `1d` for 1mo–1y · `1wk` for 2y/5y.

## MongoDB Schema

Database `finance_dashboard`, collections `stocks` and `catalog`:

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

All monetary values stored in **$M (millions)**.

`catalog` collection schema: `{ ticker, name, exchange }` — indexes on `ticker` (unique) and `exchange`.

## Frontend Features

### Navigation
- **Sticky header** — live search with 220ms debounce, dropdown autocomplete (up to 12 results)
- **Exchange tabs** — ALL / NasdaqGS / NASDAQ / NYSE / AMEX — filters both stock cards and catalog browser
- **Browse catalog** — toggle grid of all tickers in selected exchange; shows "已加入" badge if in DB

### Dashboard sections
- **Popular stocks** — auto-loads AAPL / MSFT / NVDA / TSLA / AMZN on page open (fetches from Yahoo Finance if not yet cached)
- **My stocks** — user-added tickers (popular 5 excluded), exchange-filtered, persisted in MongoDB
- **Stock cards** — ticker, name, exchange badge, current price, market cap, OCF / FCF / CAGR / FCF-conversion / **P/E** KPIs, last-updated date, refresh + delete actions

### Chart panel (click any card)

Three tabs — visibility rules:
- If the stock has cash flow data → 現金流分析 + 價格趨勢 + 多股比較 shown, opens on 現金流分析
- If no cash flow data (ETFs) → 現金流分析 tab hidden, opens directly on 價格趨勢

#### Tab 1 — 現金流分析 (Cash Flow)
- **Chart.js** bar + line combo chart:
  - Green bars — Operating Cash Flow
  - Red bars — Capital Expenditure
  - Orange bars — Interest Expense
  - Blue filled line — Free Cash Flow
- **Period toggle** (年度 / 季度) — only shown when `has_quarterly: true`; hidden for ETFs and low-data tickers
- **KPI cards** — latest OCF, FCF, OCF CAGR, FCF conversion rate
- **Data table** — full history with YoY% colour-coded green/red, FCF conversion column

#### Tab 2 — 價格趨勢 (Price Trend)
- **Stats row** — current price, period % change (green/red), period high, period low, P/E ratio (reads `kpis.pe_ratio` from MongoDB; fetches live only if not yet stored)
- **Time range buttons** — **1D** / 1M / 3M / 6M / **1Y** (default) / 2Y / 5Y
  - 1D: 5-minute bars, X-axis shows HH:MM, MA switches to MA5/MA20
  - 1M–1Y: daily bars, MA20/MA50
  - 2Y–5Y: weekly bars, MA20/MA50
- **Price chart** — blue closing price line with gradient fill + MA (yellow dashed) + MA (red dashed); legend updates dynamically
- **Volume chart** — separate bar chart below price; bars coloured green (up day) or red (down day)
- Data fetched live from Yahoo Finance on tab switch / range change (not stored in MongoDB)

#### Tab 3 — 多股比較 (Multi-ticker Comparison)
- Current ticker auto-added when tab is opened; up to 8 tickers total
- **Ticker input** — type ticker code or company name, autocomplete dropdown (up to 10 suggestions with exchange badge, same UX as header search); Enter or click to add
- **Colour-coded chips** — each ticker assigned a distinct colour; click ✕ to remove
- **Time range buttons** — 1D / 1M / 3M / 6M / 1Y (default) / 2Y / 5Y
- **Comparison chart** — Y-axis shows % change from the start of the selected period (normalised so different-priced stocks are directly comparable); tooltip shows both % change and actual price per ticker
- Data fetched live via `/api/compare` (not stored in MongoDB)

## kezsmeister/claude-finance-skills (Slash Commands)

Installed in `~/.claude/skills/` — use these in Claude Code directly:

```
/annual-revenue  <ticker>      10-yr annual revenue + YoY growth table
/quarterly-revenue <ticker>    Quarterly revenue table
/annual-eps  <ticker>          Annual diluted EPS
/quarterly-eps <ticker>        Quarterly EPS
/annual-dividend <ticker>      Annual dividends per share
/quarterly-dividend <ticker>   Quarterly dividends
/annual-capex <ticker>         Annual capital expenditure
/annual-wads <ticker>          Weighted avg diluted shares
/cashflow-chart <ticker>       Interactive HTML cash flow chart (opens in Chrome)
```

These skills require Chrome with remote debugging enabled:
```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="C:\Users\victo\AppData\Local\chrome-debug-profile"
```

MCP servers (`chrome-devtools` + `yahoo-finance`) are pre-configured in
`~/.claude/settings.json`. Restart Claude Code after first setup to activate.

## Schema Migration

`app.py` v1 stored cash flow data as flat top-level fields (`years`, `ocf`, `capex`,
`fcf`, `interest`). v2 uses a nested structure (`annual.labels`, `annual.ocf`, …).

`migrate_old_schema()` in `get_stock()` auto-detects v1 documents on first read,
converts them in-place, and writes the new layout back to MongoDB — no manual
migration needed.

## Known Limitations

- yfinance returns ~4–5 years of cash flow data by default (Yahoo Finance free tier)
- ETFs have no cash flow data — stored with `annual: null`; frontend auto-opens price trend tab
- Price history (trend tab) is fetched live; not cached in MongoDB
- 1D intraday data only available during/after market hours (yfinance limitation)
- P/E ratio may be `null` for some tickers (yfinance `fast_info` limitation)
- MongoDB must be running locally before starting Flask
- Avoid rapid batch-fetching multiple tickers (Yahoo Finance rate limiting)

## Changelog

| Version | Date       | Changes |
|---------|------------|---------|
| v1      | 2026-03-24 | Initial Flask app — single AAPL chart, flat MongoDB schema |
| v2      | 2026-03-24 | Multi-stock dashboard, NYSE/NASDAQ/AMEX catalog (312 tickers), exchange tabs, search dropdown, catalog browser, annual/quarterly toggle, popular stocks section |
| v2.1    | 2026-03-24 | Schema migration helper (`migrate_old_schema`); bug fix for MSFT/AAPL/TSLA v1 data not displaying |
| v2.2    | 2026-03-24 | Price trend tab: closing price line, MA20/MA50, volume bars, time range selector (1M–5Y), stats row (price / % change / high / low / P/E) |
| v2.3    | 2026-03-24 | ETF support: no-CF tickers stored with `annual: null`, CF tab hidden, auto-opens price trend; fixed BOTZ exchange (AMEX→NASDAQ); verified all 311 tickers against yfinance, corrected 41 exchange misclassifications, removed 4 delisted tickers (COUP/DFS/ABC/PARA), catalog now 307 tickers stored in MongoDB `catalog` collection; `server.ps1` for reliable server management; 1D time range (5-min bars, HH:MM labels, MA5/MA20) |
| v2.4    | 2026-03-24 | NasdaqGS exchange category (94 NMS-listed equities split from NASDAQ); P/E stored in `kpis.pe_ratio` (fetched via `trailingPE`/`forwardPE`), shown on stock cards and back-filled for existing records on first open; trend tab P/E reads from MongoDB instead of unreliable `fast_info` |
| v2.5    | 2026-03-25 | Multi-ticker comparison overlay chart: `/api/compare` endpoint (normalised % change), new "多股比較" tab, ticker chips with colour coding, autocomplete dropdown on ticker input (same UX as header search), up to 8 tickers, range selector 1D–5Y |
| v2.6    | 2026-03-25 | Stock screener panel: `/api/screener` (full-catalog merge — all 307 tickers, KPI filters via MongoDB `$gte`/`$lte`), `/api/sectors` endpoint, filter inputs for OCF CAGR / FCF conversion / P/E / sector / exchange, "篩選器" toggle button in tab bar, unloaded tickers show `—` KPIs with per-row "載入" button |
| v2.7    | 2026-03-25 | Bulk data loader: `/api/bulk-fetch` SSE endpoint streams per-ticker progress; "載入全部數據" button + progress bar in screener panel; skips already-loaded tickers; refreshes screener and My Stocks on completion |
| v2.8    | 2026-03-25 | Dividend history chart: `/api/stocks/<ticker>/dividends` endpoint (yfinance `t.dividends`); new "股息歷史" tab; annual bar chart (yellow); KPI stat row (trailing annual dividend, yield %, last payment); payment history table with YoY% per year; shows "不配息" message for non-dividend stocks |
| v2.9    | 2026-03-25 | Fix dividend yield display (yfinance already returns % — removed erroneous ×100); "全部清除" button in My Stocks header (clears only pinned non-popular stocks); `pinned` field on stocks documents — bulk-fetched stocks get `pinned:false` via `$setOnInsert`, user-added stocks get `pinned:true`; `GET /api/stocks` filters by `pinned != false`; `/api/stocks/<ticker>/pin` endpoint; screener click pins existing bulk-fetched stocks instead of re-fetching |
| v2.10   | 2026-03-25 | Revenue / EPS chart tab: `/api/stocks/<ticker>/financials` endpoint (yfinance `t.income_stmt` + `t.quarterly_income_stmt`); new "營收/EPS" tab; dual-axis Chart.js bar+line (Revenue bars blue left axis, Net Income bars green left axis, Diluted EPS line orange right axis); annual/quarterly toggle; KPI stat row (latest revenue, revenue CAGR, latest net income, diluted EPS); history table with YoY% colour-coded; ETFs show "無財務報表資料" message |
| v2.11   | 2026-03-25 | Export to CSV / Excel: SheetJS (xlsx@0.18.5) added via CDN; "↓ CSV" and "↓ Excel" buttons in chart panel header; exports data from whichever tab is active (CF, Rev, Div, Trend); cached `currentDivData` and `currentTrendData` globals; filename includes ticker + period; CSV uses UTF-8 BOM for Excel compatibility |
| v2.12   | 2026-03-25 | Docker Compose setup: `Dockerfile` (python:3.11-slim), `docker-compose.yml` (web + mongo:7 services, named volume `mongo_data`, healthcheck); `requirements.txt` added; `app.py` reads `MONGO_URI` env var (falls back to `localhost` for local dev); `docker compose up --build` starts everything |
| v2.13   | 2026-03-25 | Live price push via SSE: `/api/prices/stream` endpoint loops every 30s over all tracked stocks, fetches `fast_info.last_price` + `previous_close` via yfinance, streams JSON array; frontend `startPriceStream()` connects on load, calls `applyPriceUpdate()` per ticker — updates `.price` and `.price-chg` badge, triggers green/red flash animation; pulsing live dot in header shows connection state; auto-reconnects after 10s on error |

## Future Improvements

- [x] Multi-ticker comparison overlay chart
- [x] Stock screener (filter by CAGR, FCF conversion, sector)
- [x] Dividend history chart
- [x] Revenue / EPS chart tab
- [x] Export to CSV / Excel
- [x] Docker Compose setup (Flask + MongoDB together)
- [x] WebSocket live price push
