"""
Finance Dashboard v2
Flask + MongoDB + yfinance
NYSE / NASDAQ / AMEX  |  Annual & Quarterly  |  Popular stocks on load
"""

from flask import Flask, jsonify, request, render_template_string
from pymongo import MongoClient
from datetime import datetime, timezone
import yfinance as yf
import math

app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017/")
db = client["finance_dashboard"]
stocks_col  = db["stocks"]
catalog_col = db["catalog"]

# ── Stock Catalog ─────────────────────────────────────────────────
CATALOG = {
    # ── NASDAQ ───────────────────────────────────────────────────
    "AAPL":  {"name": "Apple Inc.",                    "ex": "NasdaqGS"},
    "MSFT":  {"name": "Microsoft Corporation",         "ex": "NasdaqGS"},
    "NVDA":  {"name": "NVIDIA Corporation",            "ex": "NasdaqGS"},
    "AMZN":  {"name": "Amazon.com Inc.",               "ex": "NasdaqGS"},
    "GOOGL": {"name": "Alphabet Inc. (Class A)",       "ex": "NasdaqGS"},
    "GOOG":  {"name": "Alphabet Inc. (Class C)",       "ex": "NasdaqGS"},
    "META":  {"name": "Meta Platforms Inc.",           "ex": "NasdaqGS"},
    "TSLA":  {"name": "Tesla Inc.",                    "ex": "NasdaqGS"},
    "AVGO":  {"name": "Broadcom Inc.",                 "ex": "NasdaqGS"},
    "COST":  {"name": "Costco Wholesale",              "ex": "NasdaqGS"},
    "NFLX":  {"name": "Netflix Inc.",                  "ex": "NasdaqGS"},
    "AMD":   {"name": "Advanced Micro Devices",        "ex": "NasdaqGS"},
    "INTC":  {"name": "Intel Corporation",             "ex": "NasdaqGS"},
    "QCOM":  {"name": "Qualcomm Inc.",                 "ex": "NasdaqGS"},
    "AMAT":  {"name": "Applied Materials",             "ex": "NasdaqGS"},
    "MU":    {"name": "Micron Technology",             "ex": "NasdaqGS"},
    "LRCX":  {"name": "Lam Research",                  "ex": "NasdaqGS"},
    "KLAC":  {"name": "KLA Corporation",               "ex": "NasdaqGS"},
    "ADBE":  {"name": "Adobe Inc.",                    "ex": "NasdaqGS"},
    "CRM":   {"name": "Salesforce Inc.",               "ex": "NYSE"},
    "ORCL":  {"name": "Oracle Corporation",            "ex": "NYSE"},
    "CSCO":  {"name": "Cisco Systems",                 "ex": "NasdaqGS"},
    "TXN":   {"name": "Texas Instruments",             "ex": "NasdaqGS"},
    "INTU":  {"name": "Intuit Inc.",                   "ex": "NasdaqGS"},
    "ISRG":  {"name": "Intuitive Surgical",            "ex": "NasdaqGS"},
    "GILD":  {"name": "Gilead Sciences",               "ex": "NasdaqGS"},
    "AMGN":  {"name": "Amgen Inc.",                    "ex": "NasdaqGS"},
    "BIIB":  {"name": "Biogen Inc.",                   "ex": "NasdaqGS"},
    "REGN":  {"name": "Regeneron Pharmaceuticals",     "ex": "NasdaqGS"},
    "VRTX":  {"name": "Vertex Pharmaceuticals",        "ex": "NasdaqGS"},
    "SBUX":  {"name": "Starbucks Corporation",         "ex": "NasdaqGS"},
    "MDLZ":  {"name": "Mondelez International",        "ex": "NasdaqGS"},
    "MNST":  {"name": "Monster Beverage",              "ex": "NasdaqGS"},
    "PCAR":  {"name": "PACCAR Inc.",                   "ex": "NasdaqGS"},
    "FAST":  {"name": "Fastenal Company",              "ex": "NasdaqGS"},
    "ODFL":  {"name": "Old Dominion Freight",          "ex": "NasdaqGS"},
    "MELI":  {"name": "MercadoLibre Inc.",             "ex": "NasdaqGS"},
    "ASML":  {"name": "ASML Holding",                  "ex": "NasdaqGS"},
    "ADP":   {"name": "Automatic Data Processing",     "ex": "NasdaqGS"},
    "PYPL":  {"name": "PayPal Holdings",               "ex": "NasdaqGS"},
    "CRWD":  {"name": "CrowdStrike Holdings",          "ex": "NasdaqGS"},
    "SNPS":  {"name": "Synopsys Inc.",                 "ex": "NasdaqGS"},
    "CDNS":  {"name": "Cadence Design Systems",        "ex": "NasdaqGS"},
    "PANW":  {"name": "Palo Alto Networks",            "ex": "NasdaqGS"},
    "FTNT":  {"name": "Fortinet Inc.",                 "ex": "NasdaqGS"},
    "ZS":    {"name": "Zscaler Inc.",                  "ex": "NasdaqGS"},
    "DDOG":  {"name": "Datadog Inc.",                  "ex": "NasdaqGS"},
    "SNOW":  {"name": "Snowflake Inc.",                "ex": "NYSE"},
    "PLTR":  {"name": "Palantir Technologies",         "ex": "NasdaqGS"},
    "APP":   {"name": "Applovin Corporation",          "ex": "NasdaqGS"},
    # NASDAQ – 半導體 / 硬體
    "MRVL":  {"name": "Marvell Technology",            "ex": "NasdaqGS"},
    "MCHP":  {"name": "Microchip Technology",          "ex": "NasdaqGS"},
    "ON":    {"name": "ON Semiconductor",              "ex": "NasdaqGS"},
    "SWKS":  {"name": "Skyworks Solutions",            "ex": "NasdaqGS"},
    "QRVO":  {"name": "Qorvo Inc.",                    "ex": "NasdaqGS"},
    "MPWR":  {"name": "Monolithic Power Systems",      "ex": "NasdaqGS"},
    "ENTG":  {"name": "Entegris Inc.",                 "ex": "NasdaqGS"},
    "WOLF":  {"name": "Wolfspeed Inc.",                "ex": "NYSE"},
    "SMCI":  {"name": "Super Micro Computer",          "ex": "NasdaqGS"},
    "HPE":   {"name": "Hewlett Packard Enterprise",    "ex": "NYSE"},
    "NTAP":  {"name": "NetApp Inc.",                   "ex": "NasdaqGS"},
    "WDC":   {"name": "Western Digital",               "ex": "NasdaqGS"},
    "STX":   {"name": "Seagate Technology",            "ex": "NasdaqGS"},
    # NASDAQ – 軟體 / 雲端
    "NOW":   {"name": "ServiceNow Inc.",               "ex": "NYSE"},
    "WDAY":  {"name": "Workday Inc.",                  "ex": "NasdaqGS"},
    "TEAM":  {"name": "Atlassian Corporation",         "ex": "NasdaqGS"},
    "MDB":   {"name": "MongoDB Inc.",                  "ex": "NASDAQ"},
    "OKTA":  {"name": "Okta Inc.",                     "ex": "NasdaqGS"},
    "HUBS":  {"name": "HubSpot Inc.",                  "ex": "NYSE"},
    "TTD":   {"name": "The Trade Desk",                "ex": "NASDAQ"},
    "RBLX":  {"name": "Roblox Corporation",            "ex": "NYSE"},
    "U":     {"name": "Unity Software",                "ex": "NYSE"},
    "SHOP":  {"name": "Shopify Inc.",                  "ex": "NasdaqGS"},
    "NET":   {"name": "Cloudflare Inc.",               "ex": "NYSE"},
    "TWLO":  {"name": "Twilio Inc.",                   "ex": "NYSE"},
    "ZM":    {"name": "Zoom Video Communications",     "ex": "NasdaqGS"},
    "DOCU":  {"name": "DocuSign Inc.",                 "ex": "NasdaqGS"},
    "BILL":  {"name": "Bill Holdings Inc.",            "ex": "NYSE"},
    # NASDAQ – 電商 / 消費
    "ABNB":  {"name": "Airbnb Inc.",                   "ex": "NasdaqGS"},
    "BKNG":  {"name": "Booking Holdings",              "ex": "NasdaqGS"},
    "EXPE":  {"name": "Expedia Group",                 "ex": "NasdaqGS"},
    "EBAY":  {"name": "eBay Inc.",                     "ex": "NasdaqGS"},
    "ETSY":  {"name": "Etsy Inc.",                     "ex": "NYSE"},
    "LYFT":  {"name": "Lyft Inc.",                     "ex": "NasdaqGS"},
    "UBER":  {"name": "Uber Technologies",             "ex": "NYSE"},
    "DASH":  {"name": "DoorDash Inc.",                 "ex": "NasdaqGS"},
    "SNAP":  {"name": "Snap Inc.",                     "ex": "NYSE"},
    "PINS":  {"name": "Pinterest Inc.",                "ex": "NYSE"},
    # NASDAQ – 金融 / 支付
    "COIN":  {"name": "Coinbase Global",               "ex": "NasdaqGS"},
    "HOOD":  {"name": "Robinhood Markets",             "ex": "NasdaqGS"},
    "SOFI":  {"name": "SoFi Technologies",             "ex": "NasdaqGS"},
    "AFRM":  {"name": "Affirm Holdings",               "ex": "NasdaqGS"},
    "MSTR":  {"name": "MicroStrategy Inc.",            "ex": "NasdaqGS"},
    # NASDAQ – 生技 / 醫療
    "MRNA":  {"name": "Moderna Inc.",                  "ex": "NasdaqGS"},
    "BNTX":  {"name": "BioNTech SE",                   "ex": "NasdaqGS"},
    "ILMN":  {"name": "Illumina Inc.",                 "ex": "NasdaqGS"},
    "IDXX":  {"name": "IDEXX Laboratories",            "ex": "NasdaqGS"},
    "ALGN":  {"name": "Align Technology",              "ex": "NasdaqGS"},
    # NASDAQ – 汽車 / 能源
    "RIVN":  {"name": "Rivian Automotive",             "ex": "NasdaqGS"},
    "LCID":  {"name": "Lucid Group",                   "ex": "NasdaqGS"},
    "CHPT":  {"name": "ChargePoint Holdings",          "ex": "NYSE"},
    "ENPH":  {"name": "Enphase Energy",                "ex": "NASDAQ"},
    "FSLR":  {"name": "First Solar Inc.",              "ex": "NasdaqGS"},
    "PLUG":  {"name": "Plug Power Inc.",               "ex": "NASDAQ"},
    # ── NYSE ────────────────────────────────────────────────────
    "BRK-B": {"name": "Berkshire Hathaway B",          "ex": "NYSE"},
    "JPM":   {"name": "JPMorgan Chase & Co.",          "ex": "NYSE"},
    "V":     {"name": "Visa Inc.",                     "ex": "NYSE"},
    "UNH":   {"name": "UnitedHealth Group",            "ex": "NYSE"},
    "XOM":   {"name": "Exxon Mobil Corporation",       "ex": "NYSE"},
    "JNJ":   {"name": "Johnson & Johnson",             "ex": "NYSE"},
    "WMT":   {"name": "Walmart Inc.",                  "ex": "NasdaqGS"},
    "PG":    {"name": "Procter & Gamble",              "ex": "NYSE"},
    "MA":    {"name": "Mastercard Inc.",               "ex": "NYSE"},
    "HD":    {"name": "Home Depot Inc.",               "ex": "NYSE"},
    "CVX":   {"name": "Chevron Corporation",           "ex": "NYSE"},
    "MRK":   {"name": "Merck & Co.",                   "ex": "NYSE"},
    "LLY":   {"name": "Eli Lilly and Company",         "ex": "NYSE"},
    "ABBV":  {"name": "AbbVie Inc.",                   "ex": "NYSE"},
    "BAC":   {"name": "Bank of America",               "ex": "NYSE"},
    "KO":    {"name": "Coca-Cola Company",             "ex": "NYSE"},
    "PEP":   {"name": "PepsiCo Inc.",                  "ex": "NasdaqGS"},
    "TMO":   {"name": "Thermo Fisher Scientific",      "ex": "NYSE"},
    "MCD":   {"name": "McDonald's Corporation",        "ex": "NYSE"},
    "COP":   {"name": "ConocoPhillips",                "ex": "NYSE"},
    "GE":    {"name": "GE Aerospace",                  "ex": "NYSE"},
    "CAT":   {"name": "Caterpillar Inc.",              "ex": "NYSE"},
    "GS":    {"name": "Goldman Sachs",                 "ex": "NYSE"},
    "MS":    {"name": "Morgan Stanley",                "ex": "NYSE"},
    "WFC":   {"name": "Wells Fargo & Company",         "ex": "NYSE"},
    "C":     {"name": "Citigroup Inc.",                "ex": "NYSE"},
    "AXP":   {"name": "American Express",              "ex": "NYSE"},
    "IBM":   {"name": "IBM Corporation",               "ex": "NYSE"},
    "RTX":   {"name": "RTX Corporation",               "ex": "NYSE"},
    "BA":    {"name": "Boeing Company",                "ex": "NYSE"},
    "HON":   {"name": "Honeywell International",       "ex": "NasdaqGS"},
    "UPS":   {"name": "United Parcel Service",         "ex": "NYSE"},
    "FDX":   {"name": "FedEx Corporation",             "ex": "NYSE"},
    "DE":    {"name": "Deere & Company",               "ex": "NYSE"},
    "MMM":   {"name": "3M Company",                    "ex": "NYSE"},
    "NKE":   {"name": "Nike Inc.",                     "ex": "NYSE"},
    "DIS":   {"name": "Walt Disney Company",           "ex": "NYSE"},
    "T":     {"name": "AT&T Inc.",                     "ex": "NYSE"},
    "VZ":    {"name": "Verizon Communications",        "ex": "NYSE"},
    "PM":    {"name": "Philip Morris International",   "ex": "NYSE"},
    "MO":    {"name": "Altria Group Inc.",             "ex": "NYSE"},
    "PFE":   {"name": "Pfizer Inc.",                   "ex": "NYSE"},
    "BMY":   {"name": "Bristol-Myers Squibb",          "ex": "NYSE"},
    "ABT":   {"name": "Abbott Laboratories",           "ex": "NYSE"},
    "MDT":   {"name": "Medtronic plc",                 "ex": "NYSE"},
    "SYK":   {"name": "Stryker Corporation",           "ex": "NYSE"},
    "BDX":   {"name": "Becton Dickinson",              "ex": "NYSE"},
    "NEE":   {"name": "NextEra Energy",                "ex": "NYSE"},
    "DUK":   {"name": "Duke Energy",                   "ex": "NYSE"},
    "SO":    {"name": "Southern Company",              "ex": "NYSE"},
    "D":     {"name": "Dominion Energy",               "ex": "NYSE"},
    "AMT":   {"name": "American Tower",                "ex": "NYSE"},
    "PLD":   {"name": "Prologis Inc.",                 "ex": "NYSE"},
    "CCI":   {"name": "Crown Castle Inc.",             "ex": "NYSE"},
    "SPG":   {"name": "Simon Property Group",          "ex": "NYSE"},
    # NYSE – 金融
    "BLK":   {"name": "BlackRock Inc.",                "ex": "NYSE"},
    "SCHW":  {"name": "Charles Schwab",                "ex": "NYSE"},
    "BX":    {"name": "Blackstone Inc.",               "ex": "NYSE"},
    "KKR":   {"name": "KKR & Co.",                     "ex": "NYSE"},
    "APO":   {"name": "Apollo Global Management",      "ex": "NYSE"},
    "AIG":   {"name": "American International Group",  "ex": "NYSE"},
    "MET":   {"name": "MetLife Inc.",                  "ex": "NYSE"},
    "PRU":   {"name": "Prudential Financial",          "ex": "NYSE"},
    "TRV":   {"name": "Travelers Companies",           "ex": "NYSE"},
    "CB":    {"name": "Chubb Limited",                 "ex": "NYSE"},
    "ALL":   {"name": "Allstate Corporation",          "ex": "NYSE"},
    "USB":   {"name": "U.S. Bancorp",                  "ex": "NYSE"},
    "PNC":   {"name": "PNC Financial Services",        "ex": "NYSE"},
    "TFC":   {"name": "Truist Financial",              "ex": "NYSE"},
    "COF":   {"name": "Capital One Financial",         "ex": "NYSE"},
    "SYF":   {"name": "Synchrony Financial",           "ex": "NYSE"},
    "SPGI":  {"name": "S&P Global Inc.",               "ex": "NYSE"},
    "MCO":   {"name": "Moody's Corporation",           "ex": "NYSE"},
    "ICE":   {"name": "Intercontinental Exchange",     "ex": "NYSE"},
    "CME":   {"name": "CME Group Inc.",                "ex": "NasdaqGS"},
    "CBOE":  {"name": "Cboe Global Markets",           "ex": "NYSE"},
    # NYSE – 工業 / 防衛
    "LMT":   {"name": "Lockheed Martin",               "ex": "NYSE"},
    "NOC":   {"name": "Northrop Grumman",              "ex": "NYSE"},
    "GD":    {"name": "General Dynamics",              "ex": "NYSE"},
    "LHX":   {"name": "L3Harris Technologies",         "ex": "NYSE"},
    "TDG":   {"name": "TransDigm Group",               "ex": "NYSE"},
    "ETN":   {"name": "Eaton Corporation",             "ex": "NYSE"},
    "EMR":   {"name": "Emerson Electric",              "ex": "NYSE"},
    "ROK":   {"name": "Rockwell Automation",           "ex": "NYSE"},
    "PH":    {"name": "Parker Hannifin",               "ex": "NYSE"},
    "ITW":   {"name": "Illinois Tool Works",           "ex": "NYSE"},
    "GWW":   {"name": "W.W. Grainger",                 "ex": "NYSE"},
    "XYL":   {"name": "Xylem Inc.",                    "ex": "NYSE"},
    "AME":   {"name": "AMETEK Inc.",                   "ex": "NYSE"},
    "IR":    {"name": "Ingersoll Rand",                "ex": "NYSE"},
    # NYSE – 能源
    "SLB":   {"name": "SLB (Schlumberger)",            "ex": "NYSE"},
    "HAL":   {"name": "Halliburton Company",           "ex": "NYSE"},
    "BKR":   {"name": "Baker Hughes",                  "ex": "NasdaqGS"},
    "OXY":   {"name": "Occidental Petroleum",          "ex": "NYSE"},
    "EOG":   {"name": "EOG Resources",                 "ex": "NYSE"},
    "DVN":   {"name": "Devon Energy",                  "ex": "NYSE"},
    "MPC":   {"name": "Marathon Petroleum",            "ex": "NYSE"},
    "PSX":   {"name": "Phillips 66",                   "ex": "NYSE"},
    "VLO":   {"name": "Valero Energy",                 "ex": "NYSE"},
    "KMI":   {"name": "Kinder Morgan",                 "ex": "NYSE"},
    "WMB":   {"name": "Williams Companies",            "ex": "NYSE"},
    "OKE":   {"name": "ONEOK Inc.",                    "ex": "NYSE"},
    # NYSE – 消費 / 零售
    "TGT":   {"name": "Target Corporation",            "ex": "NYSE"},
    "LOW":   {"name": "Lowe's Companies",              "ex": "NYSE"},
    "TJX":   {"name": "TJX Companies",                "ex": "NYSE"},
    "ROST":  {"name": "Ross Stores",                   "ex": "NasdaqGS"},
    "DG":    {"name": "Dollar General",                "ex": "NYSE"},
    "DLTR":  {"name": "Dollar Tree",                   "ex": "NasdaqGS"},
    "YUM":   {"name": "Yum! Brands",                   "ex": "NYSE"},
    "CMG":   {"name": "Chipotle Mexican Grill",        "ex": "NYSE"},
    "DPZ":   {"name": "Domino's Pizza",                "ex": "NasdaqGS"},
    "EL":    {"name": "Estee Lauder",                  "ex": "NYSE"},
    "CL":    {"name": "Colgate-Palmolive",             "ex": "NYSE"},
    "KMB":   {"name": "Kimberly-Clark",                "ex": "NasdaqGS"},
    "CHD":   {"name": "Church & Dwight",               "ex": "NYSE"},
    "CLX":   {"name": "Clorox Company",                "ex": "NYSE"},
    # NYSE – 醫療 / 保險
    "CVS":   {"name": "CVS Health",                    "ex": "NYSE"},
    "HUM":   {"name": "Humana Inc.",                   "ex": "NYSE"},
    "CI":    {"name": "Cigna Group",                   "ex": "NYSE"},
    "ELV":   {"name": "Elevance Health",               "ex": "NYSE"},
    "MCK":   {"name": "McKesson Corporation",          "ex": "NYSE"},
    "CAH":   {"name": "Cardinal Health",               "ex": "NYSE"},
    "BAX":   {"name": "Baxter International",          "ex": "NYSE"},
    "ZBH":   {"name": "Zimmer Biomet",                 "ex": "NYSE"},
    "BSX":   {"name": "Boston Scientific",             "ex": "NYSE"},
    "EW":    {"name": "Edwards Lifesciences",          "ex": "NYSE"},
    # NYSE – 科技 / 電信
    "ACN":   {"name": "Accenture plc",                 "ex": "NYSE"},
    "SAP":   {"name": "SAP SE",                        "ex": "NYSE"},
    "TSM":   {"name": "Taiwan Semiconductor (ADR)",    "ex": "NYSE"},
    "DELL":  {"name": "Dell Technologies",             "ex": "NYSE"},
    "HPQ":   {"name": "HP Inc.",                       "ex": "NYSE"},
    "TMUS":  {"name": "T-Mobile US",                   "ex": "NasdaqGS"},
    "WBD":   {"name": "Warner Bros. Discovery",        "ex": "NasdaqGS"},
    "F":     {"name": "Ford Motor Company",            "ex": "NYSE"},
    "GM":    {"name": "General Motors",                "ex": "NYSE"},
    "STLA":  {"name": "Stellantis N.V.",               "ex": "NYSE"},
    # ── AMEX ────────────────────────────────────────────────────
    "SPY":   {"name": "SPDR S&P 500 ETF",             "ex": "AMEX"},
    "QQQ":   {"name": "Invesco QQQ Trust (NASDAQ)",    "ex": "NASDAQ"},
    "IWM":   {"name": "iShares Russell 2000 ETF",      "ex": "AMEX"},
    "DIA":   {"name": "SPDR Dow Jones Industrial",     "ex": "AMEX"},
    "GLD":   {"name": "SPDR Gold Shares",              "ex": "AMEX"},
    "SLV":   {"name": "iShares Silver Trust",          "ex": "AMEX"},
    "IAU":   {"name": "iShares Gold Trust",            "ex": "AMEX"},
    "USO":   {"name": "United States Oil Fund",        "ex": "AMEX"},
    "UNG":   {"name": "United States Natural Gas",     "ex": "AMEX"},
    "XLE":   {"name": "Energy Select Sector SPDR",     "ex": "AMEX"},
    "XLF":   {"name": "Financial Select Sector SPDR",  "ex": "AMEX"},
    "XLK":   {"name": "Technology Select Sector SPDR", "ex": "AMEX"},
    "XLV":   {"name": "Health Care Select Sector",     "ex": "AMEX"},
    "XLI":   {"name": "Industrial Select Sector",      "ex": "AMEX"},
    "XLY":   {"name": "Consumer Discret. Select",      "ex": "AMEX"},
    "XLP":   {"name": "Consumer Staples Select",       "ex": "AMEX"},
    "XLU":   {"name": "Utilities Select Sector",       "ex": "AMEX"},
    "XLB":   {"name": "Materials Select Sector",       "ex": "AMEX"},
    "XLRE":  {"name": "Real Estate Select Sector",     "ex": "AMEX"},
    "ARKK":  {"name": "ARK Innovation ETF",            "ex": "AMEX"},
    "ARKG":  {"name": "ARK Genomic Revolution ETF",    "ex": "AMEX"},
    "ARKW":  {"name": "ARK Next Gen Internet ETF",     "ex": "AMEX"},
    "VTI":   {"name": "Vanguard Total Stock Market",   "ex": "AMEX"},
    "VOO":   {"name": "Vanguard S&P 500 ETF",          "ex": "AMEX"},
    "VGT":   {"name": "Vanguard IT ETF",               "ex": "AMEX"},
    "SCHD":  {"name": "Schwab US Dividend Equity ETF", "ex": "AMEX"},
    "JEPI":  {"name": "JPMorgan Equity Premium",       "ex": "AMEX"},
    "TQQQ":  {"name": "ProShares UltraPro QQQ",        "ex": "NASDAQ"},
    "SQQQ":  {"name": "ProShares UltraPro Short QQQ",  "ex": "NASDAQ"},
    "TLT":   {"name": "iShares 20+ Year Treasury",     "ex": "NASDAQ"},
    "HYG":   {"name": "iShares iBoxx High Yield ETF",  "ex": "AMEX"},
    # AMEX – 債券 ETF
    "IEF":   {"name": "iShares 7-10 Year Treasury",   "ex": "NASDAQ"},
    "SHY":   {"name": "iShares 1-3 Year Treasury",    "ex": "NASDAQ"},
    "BND":   {"name": "Vanguard Total Bond Market",   "ex": "NASDAQ"},
    "AGG":   {"name": "iShares Core US Agg Bond",     "ex": "AMEX"},
    "LQD":   {"name": "iShares iBoxx Inv Grade ETF",  "ex": "AMEX"},
    "EMB":   {"name": "iShares JP Morgan EM Bond",    "ex": "NASDAQ"},
    # AMEX – 股票 ETF (市場)
    "VEA":   {"name": "Vanguard Developed Markets",   "ex": "AMEX"},
    "VWO":   {"name": "Vanguard Emerging Markets",    "ex": "AMEX"},
    "EFA":   {"name": "iShares MSCI EAFE ETF",        "ex": "AMEX"},
    "EEM":   {"name": "iShares MSCI Emerging Markets","ex": "AMEX"},
    "VNQ":   {"name": "Vanguard Real Estate ETF",     "ex": "AMEX"},
    "IYR":   {"name": "iShares US Real Estate ETF",   "ex": "AMEX"},
    # AMEX – 槓桿 / 反向
    "UPRO":  {"name": "ProShares UltraPro S&P500",    "ex": "AMEX"},
    "SPXU":  {"name": "ProShares UltraPro Short S&P", "ex": "AMEX"},
    "LABU":  {"name": "Direxion Daily S&P Bio Bull",  "ex": "AMEX"},
    "SOXL":  {"name": "Direxion Daily Semi Bull 3x",  "ex": "AMEX"},
    "SOXS":  {"name": "Direxion Daily Semi Bear 3x",  "ex": "AMEX"},
    "TECL":  {"name": "Direxion Daily Tech Bull 3x",  "ex": "AMEX"},
    "FNGU":  {"name": "MicroSectors FANG+ Bull 3x",   "ex": "AMEX"},
    # AMEX – 商品 / 實物
    "PDBC":  {"name": "Invesco Optimum Yield Cmdty",  "ex": "NASDAQ"},
    "CORN":  {"name": "Teucrium Corn Fund",           "ex": "AMEX"},
    "WEAT":  {"name": "Teucrium Wheat Fund",          "ex": "AMEX"},
    "CPER":  {"name": "United States Copper Index",   "ex": "AMEX"},
    "URA":   {"name": "Global X Uranium ETF",         "ex": "AMEX"},
    "REMX":  {"name": "VanEck Rare Earth/Strat Met",  "ex": "AMEX"},
    # AMEX – 主題 ETF
    "BOTZ":  {"name": "Global X Robotics & AI ETF",   "ex": "NASDAQ"},
    "ROBO":  {"name": "ROBO Global Robotics ETF",     "ex": "AMEX"},
    "CLOU":  {"name": "Global X Cloud Computing ETF", "ex": "NASDAQ"},
    "FINX":  {"name": "Global X FinTech ETF",         "ex": "NASDAQ"},
    "BLOK":  {"name": "Amplify Transformational Data","ex": "AMEX"},
    "BITO":  {"name": "ProShares Bitcoin Strategy",   "ex": "AMEX"},
    "GBTC":  {"name": "Grayscale Bitcoin Trust",      "ex": "AMEX"},
    "ETHE":  {"name": "Grayscale Ethereum Trust",     "ex": "AMEX"},
    "ICLN":  {"name": "iShares Global Clean Energy",  "ex": "NASDAQ"},
    "QCLN":  {"name": "First Trust NASDAQ CleanEdge", "ex": "NASDAQ"},
    "TAN":   {"name": "Invesco Solar ETF",            "ex": "AMEX"},
    "FAN":   {"name": "First Trust Global Wind Energy","ex": "AMEX"},
}

POPULAR_TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"]


# ── Helpers ───────────────────────────────────────────────────────

def safe(val):
    try:
        v = float(val)
        return None if math.isnan(v) or math.isinf(v) else round(v, 2)
    except Exception:
        return None


def extract_series(df, qdf, *kw_groups):
    """Find a row in df matching all keywords in any kw_group."""
    def find(frame):
        if frame is None or frame.empty:
            return None
        for kws in kw_groups:
            for k in frame.index:
                if all(w.lower() in k.lower() for w in kws):
                    return k
        return None
    return find(df), find(qdf)


def build_period_data(cf, income, quarterly=False):
    """Extract OCF/CapEx/FCF/Interest arrays from a cashflow+income dataframe pair."""
    if cf is None or cf.empty:
        return None

    ocf_k,  q_ocf_k  = extract_series(cf,     cf,     ("operating", "cash"),    ("Operating Cash Flow",))
    cap_k,  q_cap_k  = extract_series(cf,     cf,     ("capital", "expenditure"),("Capital Expenditure",))
    fcf_k,  q_fcf_k  = extract_series(cf,     cf,     ("free", "cash"),)
    int_k,  q_int_k  = extract_series(income, income, ("interest", "expense"),) if income is not None and not income.empty else (None, None)

    key_ocf  = ocf_k
    key_cap  = cap_k
    key_fcf  = fcf_k
    key_int  = int_k

    labels, ocf_v, cap_v, fcf_v, int_v = [], [], [], [], []

    for col in reversed(cf.columns):
        if quarterly:
            labels.append(f"Q{((col.month - 1) // 3) + 1}'{str(col.year)[2:]}")
        else:
            labels.append(f"FY{col.year}")

        def get(key, frame, divisor=1e6, absolute=False):
            if key and key in frame.index and col in frame.columns:
                v = safe(frame.loc[key, col])
                if v is not None:
                    v = round(v / divisor, 2)
                    return round(abs(v), 2) if absolute else v
            return None

        o = get(key_ocf, cf)
        c = get(key_cap, cf, absolute=True)
        f = get(key_fcf, cf)
        i = get(key_int, income, absolute=True) if income is not None and not income.empty else None

        if f is None and o is not None and c is not None:
            f = round(o - c, 2)

        ocf_v.append(o); cap_v.append(c); fcf_v.append(f); int_v.append(i)

    return {"labels": labels, "ocf": ocf_v, "capex": cap_v, "fcf": fcf_v, "interest": int_v}


def compute_kpis(series):
    valid_ocf = [v for v in series["ocf"] if v is not None and v > 0]
    valid_fcf = [v for v in series["fcf"] if v is not None]

    latest_ocf = valid_ocf[-1] if valid_ocf else None
    latest_fcf = valid_fcf[-1] if valid_fcf else None
    cagr = None
    if len(valid_ocf) >= 2:
        n = len(valid_ocf) - 1
        try:
            cagr = round(((valid_ocf[-1] / valid_ocf[0]) ** (1 / n) - 1) * 100, 2)
        except Exception:
            pass
    fcf_conv = round(latest_fcf / latest_ocf * 100, 1) if latest_fcf and latest_ocf else None

    return {
        "latest_ocf": latest_ocf,
        "latest_fcf": latest_fcf,
        "ocf_cagr": cagr,
        "fcf_conversion": fcf_conv,
    }


def fetch_stock(ticker_symbol: str) -> dict:
    sym = ticker_symbol.upper()
    t = yf.Ticker(sym)
    info = t.info

    name = info.get("longName") or info.get("shortName") or CATALOG.get(sym, {}).get("name") or sym
    exchange = CATALOG.get(sym, {}).get("ex") or info.get("exchange", "")
    sector = info.get("sector", "")
    industry = info.get("industry", "")
    currency = info.get("currency", "USD")
    current_price = safe(info.get("currentPrice") or info.get("regularMarketPrice"))
    market_cap = safe(info.get("marketCap"))
    pe_ratio = safe(info.get("trailingPE") or info.get("forwardPE"))

    # Annual (may be None for ETFs)
    annual = build_period_data(t.cashflow, t.income_stmt)

    # Quarterly
    qcf = t.quarterly_cashflow
    qinc = t.quarterly_income_stmt
    quarterly = build_period_data(qcf, qinc, quarterly=True) if qcf is not None and not qcf.empty else None

    kpis = compute_kpis(annual) if annual else {}

    return {
        "ticker": sym,
        "name": name,
        "exchange": exchange,
        "sector": sector,
        "industry": industry,
        "currency": currency,
        "current_price": current_price,
        "market_cap": market_cap,
        "annual": annual,
        "quarterly": quarterly,
        "has_quarterly": quarterly is not None,
        "kpis": {**kpis, "pe_ratio": pe_ratio},
        "last_updated": datetime.now(timezone.utc),
    }


# ── REST API ──────────────────────────────────────────────────────

@app.route("/api/catalog")
def catalog():
    VALID_EX = {"NasdaqGS", "NASDAQ", "NYSE", "AMEX"}
    ex_raw = request.args.get("exchange", "")
    ex = next((v for v in VALID_EX if v.upper() == ex_raw.upper()), ex_raw)
    q  = request.args.get("q", "").lower()
    query = {}
    if ex:
        query["exchange"] = ex
    if q:
        import re as _re
        pattern = _re.compile(_re.escape(q), _re.IGNORECASE)
        query["$or"] = [{"ticker": pattern}, {"name": pattern}]
    docs = list(catalog_col.find(query, {"_id": 0}).sort("ticker", 1))
    in_db_set = {d["ticker"] for d in stocks_col.find({}, {"ticker": 1, "_id": 0})}
    for doc in docs:
        doc["in_db"] = doc["ticker"] in in_db_set
    return jsonify(docs)


@app.route("/api/stocks")
def list_stocks():
    docs = list(stocks_col.find({}, {"_id": 0,
        "ticker": 1, "name": 1, "exchange": 1, "sector": 1,
        "current_price": 1, "market_cap": 1, "kpis": 1,
        "has_quarterly": 1, "last_updated": 1}).sort("ticker", 1))
    return jsonify(docs)


@app.route("/api/stocks", methods=["POST"])
def add_stock():
    body = request.get_json(force=True)
    ticker = body.get("ticker", "").strip().upper()
    if not ticker:
        return jsonify({"error": "ticker is required"}), 400
    try:
        data = fetch_stock(ticker)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    stocks_col.update_one({"ticker": ticker}, {"$set": data}, upsert=True)
    return jsonify({"ok": True, "ticker": ticker, "name": data["name"]}), 201


def migrate_old_schema(doc: dict) -> dict:
    """Convert v1 flat schema (years/ocf/capex/fcf/interest) to v2 nested schema."""
    if doc.get("annual") is not None:
        return doc  # already v2
    if "years" not in doc:
        return doc  # unknown, return as-is
    annual = {
        "labels":   doc.pop("years", []),
        "ocf":      doc.pop("ocf", []),
        "capex":    doc.pop("capex", []),
        "fcf":      doc.pop("fcf", []),
        "interest": doc.pop("interest", []),
    }
    doc["annual"] = annual
    doc["quarterly"] = None
    doc["has_quarterly"] = False
    # persist migration
    stocks_col.update_one(
        {"ticker": doc["ticker"]},
        {"$set": {"annual": annual, "quarterly": None, "has_quarterly": False},
         "$unset": {"years": "", "ocf": "", "capex": "", "fcf": "", "interest": ""}}
    )
    return doc


@app.route("/api/stocks/<ticker>")
def get_stock(ticker):
    doc = stocks_col.find_one({"ticker": ticker.upper()}, {"_id": 0})
    if not doc:
        return jsonify({"error": "not found"}), 404
    doc = migrate_old_schema(doc)
    # Back-fill P/E for existing records that don't have it
    if doc.get("kpis") is not None and doc["kpis"].get("pe_ratio") is None:
        try:
            info = yf.Ticker(ticker.upper()).info
            pe = safe(info.get("trailingPE") or info.get("forwardPE"))
            if pe is not None:
                doc["kpis"]["pe_ratio"] = pe
                stocks_col.update_one({"ticker": ticker.upper()}, {"$set": {"kpis.pe_ratio": pe}})
        except Exception:
            pass
    return jsonify(doc)


@app.route("/api/stocks/<ticker>", methods=["DELETE"])
def delete_stock(ticker):
    r = stocks_col.delete_one({"ticker": ticker.upper()})
    return (jsonify({"ok": True}) if r.deleted_count else jsonify({"error": "not found"}), 404)


@app.route("/api/stocks/<ticker>/history")
def stock_history(ticker):
    """Price history + volume + MA20 + MA50 for trend chart."""
    period   = request.args.get("period", "1y")   # 1d 1mo 3mo 6mo 1y 2y 5y
    if period == "1d":
        interval = "5m"
    elif period in ("1mo","3mo","6mo","1y"):
        interval = "1d"
    else:
        interval = "1wk"
    try:
        t    = yf.Ticker(ticker.upper())
        hist = t.history(period=period, interval=interval)
        if hist.empty:
            return jsonify({"error": "no price data"}), 404

        closes  = hist["Close"].round(2).tolist()
        volumes = hist["Volume"].tolist()
        highs   = hist["High"].round(2).tolist()
        lows    = hist["Low"].round(2).tolist()
        if period == "1d":
            dates = [d.strftime("%H:%M") for d in hist.index]
        else:
            dates = [d.strftime("%Y-%m-%d") for d in hist.index]

        # Moving averages
        def ma(n):
            result = []
            for i in range(len(closes)):
                if i < n - 1:
                    result.append(None)
                else:
                    result.append(round(sum(closes[i-n+1:i+1]) / n, 2))
            return result

        # Price stats
        c_latest  = closes[-1]  if closes  else None
        c_first   = closes[0]   if closes  else None
        pct_chg   = round((c_latest - c_first) / c_first * 100, 2) if c_first else None
        high_52w  = round(max(h for h in highs  if h), 2) if highs  else None
        low_52w   = round(min(l for l in lows   if l), 2) if lows   else None

        # P/E: prefer stored value in MongoDB, fallback to yfinance info
        db_doc = stocks_col.find_one({"ticker": ticker.upper()}, {"kpis.pe_ratio": 1, "_id": 0})
        pe = db_doc.get("kpis", {}).get("pe_ratio") if db_doc else None
        if pe is None:
            try:
                full_info = t.info
                pe = safe(full_info.get("trailingPE") or full_info.get("forwardPE"))
            except Exception:
                pe = None

        return jsonify({
            "ticker":   ticker.upper(),
            "period":   period,
            "interval": interval,
            "dates":    dates,
            "close":    closes,
            "volume":   volumes,
            "ma20":     ma(5)  if period == "1d" else ma(20),
            "ma50":     ma(20) if period == "1d" else ma(50),
            "ma_labels": ["MA5","MA20"] if period == "1d" else ["MA20","MA50"],
            "stats": {
                "latest_price": c_latest,
                "pct_change":   pct_chg,
                "high_52w":     high_52w,
                "low_52w":      low_52w,
                "pe_ratio":     pe,
            },
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/stocks/<ticker>/refresh", methods=["POST"])
def refresh_stock(ticker):
    try:
        data = fetch_stock(ticker.upper())
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    stocks_col.update_one({"ticker": ticker.upper()}, {"$set": data}, upsert=True)
    return jsonify({"ok": True, "name": data["name"]})


@app.route("/api/popular")
def popular():
    """Return popular tickers, fetching if not in DB."""
    result = []
    for sym in POPULAR_TICKERS:
        doc = stocks_col.find_one({"ticker": sym}, {"_id": 0,
            "ticker": 1, "name": 1, "exchange": 1, "sector": 1,
            "current_price": 1, "market_cap": 1, "kpis": 1, "has_quarterly": 1})
        if not doc:
            try:
                data = fetch_stock(sym)
                stocks_col.update_one({"ticker": sym}, {"$set": data}, upsert=True)
                doc = {k: data[k] for k in ["ticker","name","exchange","sector",
                    "current_price","market_cap","kpis","has_quarterly"]}
            except Exception:
                continue
        result.append(doc)
    return jsonify(result)


# ── HTML ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML)


HTML = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Finance Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0f0f1a; --card:#16213e; --panel:#0f172a; --border:#1e293b;
  --accent:#3b82f6; --text:#cdd6f4; --muted:#94a3b8; --dim:#475569;
  --green:#4ade80; --red:#f87171; --orange:#fbbf24; --blue:#60a5fa; --purple:#a78bfa;
}
body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh}

/* ── Header ────────────────────────── */
header{
  background:var(--card);border-bottom:1px solid var(--border);
  padding:14px 24px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;
  position:sticky;top:0;z-index:100
}
header h1{font-size:1.2rem;color:#e2e8f0;flex:0 0 auto}
.header-sep{flex:1}
.search-wrap{position:relative;flex:0 0 260px}
.search-wrap input{
  width:100%;background:var(--panel);border:1px solid var(--border);
  color:var(--text);padding:7px 14px 7px 36px;border-radius:8px;font-size:.88rem;outline:none;
}
.search-wrap input:focus{border-color:var(--accent)}
.search-wrap .ico{position:absolute;left:11px;top:50%;transform:translateY(-50%);color:var(--dim);font-size:.9rem}
#dropdown{
  position:absolute;top:calc(100% + 4px);left:0;right:0;
  background:var(--card);border:1px solid var(--border);border-radius:8px;
  max-height:260px;overflow-y:auto;z-index:200;display:none
}
#dropdown .dd-item{
  padding:9px 14px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;
  font-size:.84rem;border-bottom:1px solid var(--border);
}
#dropdown .dd-item:hover{background:var(--panel)}
#dropdown .dd-item:last-child{border-bottom:none}
.dd-ex{font-size:.7rem;padding:2px 7px;border-radius:20px;font-weight:600}
.dd-ex.NasdaqGS{background:#0f2d4a;color:#38bdf8}
.dd-ex.NASDAQ{background:#1e3a5f;color:#60a5fa}
.dd-ex.NYSE{background:#1a2e1a;color:#4ade80}
.dd-ex.AMEX{background:#2e1a2e;color:#a78bfa}
.dd-in{font-size:.7rem;color:var(--dim)}

/* ── Exchange Tabs ──────────────────── */
.ex-tabs{display:flex;gap:6px;padding:16px 24px 0}
.ex-tab{
  padding:7px 18px;border-radius:8px;border:1px solid var(--border);
  background:var(--card);color:var(--muted);cursor:pointer;font-size:.82rem;font-weight:600;transition:.15s
}
.ex-tab:hover{border-color:var(--accent);color:var(--text)}
.ex-tab.active{background:var(--accent);border-color:var(--accent);color:#fff}

/* ── Main Layout ────────────────────── */
main{padding:20px 24px}
section{margin-bottom:28px}
section h2{font-size:.88rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:14px;font-weight:600}

/* ── Stock Grid ─────────────────────── */
.stock-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.stock-card{
  background:var(--card);border-radius:12px;padding:16px;cursor:pointer;
  border:2px solid transparent;transition:.15s
}
.stock-card:hover{border-color:#334155}
.stock-card.active{border-color:var(--accent)}
.card-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px}
.card-ticker{font-size:1.25rem;font-weight:700;color:#e2e8f0}
.card-name{font-size:.76rem;color:var(--muted);margin-top:2px;max-width:180px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card-price{text-align:right}
.card-price .price{font-size:1.05rem;font-weight:600;color:var(--green)}
.ex-badge{font-size:.68rem;padding:2px 7px;border-radius:20px;font-weight:600;display:inline-block;margin-top:4px}
.ex-badge.NasdaqGS{background:#0f2d4a;color:#38bdf8}
.ex-badge.NASDAQ{background:#1e3a5f;color:#60a5fa}
.ex-badge.NYSE{background:#1a2e1a;color:#4ade80}
.ex-badge.AMEX{background:#2e1a2e;color:#a78bfa}
.kpi-row{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}
.kpi{background:var(--panel);border-radius:7px;padding:7px 9px;flex:1;min-width:70px}
.kpi .v{font-size:.9rem;font-weight:700}
.kpi .l{font-size:.62rem;color:var(--dim);text-transform:uppercase;margin-top:1px}
.card-footer{display:flex;gap:6px;align-items:center;margin-top:10px}
.btn{padding:5px 12px;border:none;border-radius:6px;cursor:pointer;font-size:.75rem;font-weight:600;transition:.15s}
.btn-refresh{background:var(--panel);color:#93c5fd}.btn-refresh:hover{background:#1e3a5f}
.btn-del{background:#450a0a;color:#fca5a5}.btn-del:hover{background:#7f1d1d}
.updated{flex:1;text-align:right;font-size:.65rem;color:var(--dim)}
.spinner-inline{display:inline-block;width:12px;height:12px;border:2px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .6s linear infinite;vertical-align:middle}
@keyframes spin{to{transform:rotate(360deg)}}

/* ── Chart Panel ────────────────────── */
#chart-panel{background:var(--card);border-radius:14px;padding:22px;margin-bottom:24px;display:none}
.chart-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:10px}
.chart-header h3{font-size:1.1rem;color:#e2e8f0}
.period-toggle{display:flex;gap:4px}
.period-btn{padding:5px 14px;border-radius:7px;border:1px solid var(--border);background:var(--panel);color:var(--muted);cursor:pointer;font-size:.8rem;font-weight:600;transition:.15s}
.period-btn.active{background:var(--accent);border-color:var(--accent);color:#fff}
.chart-wrap{height:420px;position:relative;margin-bottom:18px}
.kpi-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:18px}
.kpi-card{background:var(--panel);border-radius:9px;padding:13px;text-align:center}
.kpi-card .v{font-size:1.25rem;font-weight:700;margin-bottom:3px}
.kpi-card .l{font-size:.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.kpi-card .s{font-size:.68rem;color:var(--dim);margin-top:2px}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.8rem}
th{background:var(--panel);padding:8px 12px;text-align:left;color:var(--muted);font-size:.7rem;text-transform:uppercase;letter-spacing:.04em;white-space:nowrap;position:sticky;top:0}
td{padding:7px 12px;border-bottom:1px solid var(--border);white-space:nowrap}
tr:hover td{background:#1e293b}

/* ── View tabs (現金流 / 趨勢) ───────── */
.view-tabs{display:flex;gap:2px;background:var(--panel);border-radius:9px;padding:3px;margin-bottom:16px}
.view-tab{flex:1;padding:6px 0;text-align:center;border-radius:7px;border:none;background:transparent;color:var(--muted);cursor:pointer;font-size:.82rem;font-weight:600;transition:.15s}
.view-tab.active{background:var(--card);color:var(--text);box-shadow:0 1px 4px rgba(0,0,0,.4)}
/* ── Trend section ───────────────────── */
#trend-section{display:none}
.range-row{display:flex;gap:5px;margin-bottom:14px;flex-wrap:wrap;align-items:center}
.range-btn{padding:4px 13px;border-radius:6px;border:1px solid var(--border);background:var(--panel);color:var(--muted);cursor:pointer;font-size:.76rem;font-weight:600;transition:.15s}
.range-btn.active{background:var(--accent);border-color:var(--accent);color:#fff}
.trend-wrap{height:380px;position:relative;margin-bottom:14px}
.vol-wrap{height:120px;position:relative;margin-bottom:18px}
.stat-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin-bottom:4px}
.stat-card{background:var(--panel);border-radius:8px;padding:11px 14px}
.stat-card .v{font-size:1.15rem;font-weight:700;margin-bottom:2px}
.stat-card .l{font-size:.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
/* ── Catalog panel ──────────────────── */
#catalog-panel{background:var(--card);border-radius:14px;padding:20px;margin-bottom:24px;display:none}
#catalog-panel h3{font-size:.9rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:12px}
.cat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:8px;max-height:340px;overflow-y:auto}
.cat-item{
  display:flex;justify-content:space-between;align-items:center;
  background:var(--panel);border-radius:8px;padding:8px 12px;cursor:pointer;border:1px solid transparent;transition:.15s
}
.cat-item:hover{border-color:var(--accent)}
.cat-item.in-db{border-color:#1e3a5f}
.cat-ticker{font-weight:700;font-size:.88rem;color:#e2e8f0}
.cat-name{font-size:.7rem;color:var(--muted);margin-top:2px;max-width:130px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cat-add{background:var(--accent);color:#fff;border:none;border-radius:5px;padding:3px 8px;font-size:.7rem;cursor:pointer;white-space:nowrap}
.cat-add:disabled{background:var(--border);color:var(--dim);cursor:not-allowed}
.cat-added{font-size:.7rem;color:var(--green)}

/* ── Toast ──────────────────────────── */
.toast{position:fixed;bottom:22px;right:22px;background:var(--card);border:1px solid var(--border);color:var(--text);padding:11px 18px;border-radius:9px;font-size:.83rem;z-index:999;opacity:0;transition:.3s;pointer-events:none;max-width:300px}
.toast.show{opacity:1}
.empty-msg{text-align:center;padding:40px;color:var(--dim);font-size:.9rem}
</style>
</head>
<body>

<header>
  <h1>Finance Dashboard</h1>
  <div class="header-sep"></div>
  <!-- Search box -->
  <div class="search-wrap">
    <span class="ico">&#128269;</span>
    <input id="searchInput" placeholder="搜尋股票代碼或公司名稱..." autocomplete="off">
    <div id="dropdown"></div>
  </div>
</header>

<!-- Exchange filter tabs -->
<div class="ex-tabs">
  <button class="ex-tab active" data-ex="ALL"      onclick="setExchange(this)">全部</button>
  <button class="ex-tab" data-ex="NasdaqGS" onclick="setExchange(this)">NasdaqGS</button>
  <button class="ex-tab" data-ex="NASDAQ"   onclick="setExchange(this)">NASDAQ</button>
  <button class="ex-tab" data-ex="NYSE"     onclick="setExchange(this)">NYSE</button>
  <button class="ex-tab" data-ex="AMEX"     onclick="setExchange(this)">AMEX</button>
  <button class="ex-tab" style="margin-left:auto;background:#1a2e1a;border-color:#2d4a2d;color:#4ade80" onclick="toggleCatalog()">+ 瀏覽股票目錄</button>
</div>

<main>
  <!-- Catalog browser -->
  <div id="catalog-panel">
    <h3 id="catalog-title">NYSE 股票目錄</h3>
    <div class="cat-grid" id="catGrid"></div>
  </div>

  <!-- Chart panel -->
  <div id="chart-panel">
    <div class="chart-header">
      <h3 id="chart-title"></h3>
      <div class="period-toggle" id="periodToggle" style="display:none">
        <button class="period-btn active" id="btnAnnual" onclick="setPeriod('annual')">年度</button>
        <button class="period-btn" id="btnQuarterly" onclick="setPeriod('quarterly')">季度</button>
      </div>
    </div>
    <!-- View switcher -->
    <div class="view-tabs">
      <button class="view-tab active" id="tabCF"    onclick="setView('cf')">現金流分析</button>
      <button class="view-tab"        id="tabTrend" onclick="setView('trend')">價格趨勢</button>
    </div>

    <!-- Cash flow view -->
    <div id="cf-section">
      <div class="chart-wrap"><canvas id="cfChart"></canvas></div>
      <div class="kpi-cards" id="kpiCards"></div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>期間</th>
              <th style="color:var(--green)">營業現金流</th>
              <th>YoY%</th>
              <th style="color:var(--red)">資本支出</th>
              <th style="color:var(--orange)">利息費用</th>
              <th style="color:var(--blue)">自由現金流</th>
              <th style="color:var(--purple)">FCF 轉換率</th>
            </tr>
          </thead>
          <tbody id="chartTable"></tbody>
        </table>
      </div>
    </div>

    <!-- Trend view -->
    <div id="trend-section">
      <div class="stat-row" id="trendStats"></div>
      <div class="range-row">
        <span style="font-size:.75rem;color:var(--muted);margin-right:4px">區間：</span>
        <button class="range-btn" data-p="1d"   onclick="setRange(this)">1D</button>
        <button class="range-btn" data-p="1mo"  onclick="setRange(this)">1M</button>
        <button class="range-btn" data-p="3mo"  onclick="setRange(this)">3M</button>
        <button class="range-btn" data-p="6mo"  onclick="setRange(this)">6M</button>
        <button class="range-btn active" data-p="1y" onclick="setRange(this)">1Y</button>
        <button class="range-btn" data-p="2y"   onclick="setRange(this)">2Y</button>
        <button class="range-btn" data-p="5y"   onclick="setRange(this)">5Y</button>
        <span style="margin-left:10px;font-size:.72rem;color:var(--dim)" id="maLegend">
          <span style="color:#60a5fa">&#9644;</span> 收盤價 &nbsp;
          <span style="color:#fbbf24">&#9644;</span> MA20 &nbsp;
          <span style="color:#f87171">&#9644;</span> MA50
        </span>
      </div>
      <div class="trend-wrap"><canvas id="trendChart"></canvas></div>
      <div style="font-size:.72rem;color:var(--muted);margin-bottom:6px">成交量</div>
      <div class="vol-wrap"><canvas id="volChart"></canvas></div>
    </div>
  </div>

  <!-- Popular stocks -->
  <section id="popularSection">
    <h2>熱門股票</h2>
    <div class="stock-grid" id="popularGrid"><div class="empty-msg"><span class="spinner-inline"></span> 載入中...</div></div>
  </section>

  <!-- My stocks -->
  <section id="mySection">
    <h2>我的股票</h2>
    <div class="stock-grid" id="myGrid"><div class="empty-msg">尚無自訂股票。從搜尋或目錄新增。</div></div>
  </section>
</main>
<div class="toast" id="toast"></div>

<script>
Chart.register(ChartDataLabels);

let cfChart    = null;
let trendChart = null;
let volChart   = null;
let currentTicker    = null;
let currentPeriod    = 'annual';
let currentView      = 'cf';
let currentRange     = '1y';
let currentExchange  = 'ALL';
let currentStockData = null;
let catalogVisible   = false;
let searchDebounce   = null;

// ── Format helpers ────────────────────────────────────────────
function fmt(v){
  if(v==null) return 'N/A';
  const a=Math.abs(v);
  if(a>=1000) return `$${(v/1000).toFixed(2)}B`;
  return `$${v.toFixed(0)}M`;
}
function fmtCap(v){
  if(v==null) return 'N/A';
  if(v>=1e12) return `$${(v/1e12).toFixed(2)}T`;
  if(v>=1e9)  return `$${(v/1e9).toFixed(2)}B`;
  if(v>=1e6)  return `$${(v/1e6).toFixed(1)}M`;
  return `$${v}`;
}
function toast(msg){
  const el=document.getElementById('toast');
  el.textContent=msg; el.classList.add('show');
  setTimeout(()=>el.classList.remove('show'),2800);
}

// ── Exchange filter ───────────────────────────────────────────
function setExchange(btn){
  document.querySelectorAll('.ex-tab[data-ex]').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  currentExchange = btn.dataset.ex;
  loadMyStocks();
  if(catalogVisible) loadCatalog();
}

// ── Catalog browser ───────────────────────────────────────────
async function toggleCatalog(){
  catalogVisible = !catalogVisible;
  document.getElementById('catalog-panel').style.display = catalogVisible ? 'block' : 'none';
  if(catalogVisible) loadCatalog();
}

async function loadCatalog(){
  const ex = currentExchange === 'ALL' ? 'NasdaqGS' : currentExchange;
  document.getElementById('catalog-title').textContent = `${ex} 股票目錄`;
  const res = await fetch(`/api/catalog?exchange=${ex}`);
  const items = await res.json();
  const grid = document.getElementById('catGrid');
  grid.innerHTML = items.map(s=>`
    <div class="cat-item ${s.in_db?'in-db':''}" id="catitem-${s.ticker}">
      <div>
        <div class="cat-ticker">${s.ticker}</div>
        <div class="cat-name">${s.name}</div>
      </div>
      ${s.in_db
        ? `<span class="cat-added">已加入</span>`
        : `<button class="cat-add" id="catadd-${s.ticker}" onclick="addFromCatalog('${s.ticker}')">+ 加入</button>`
      }
    </div>`).join('');
}

async function addFromCatalog(ticker){
  const btn = document.getElementById('catadd-'+ticker);
  if(btn){ btn.disabled=true; btn.textContent='載入...'; }
  const res = await fetch('/api/stocks', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ticker})
  });
  const d = await res.json();
  if(!res.ok){ toast('Error: '+d.error); if(btn){btn.disabled=false;btn.textContent='+ 加入';} return; }
  toast(`已加入 ${d.name}`);
  const item = document.getElementById('catitem-'+ticker);
  if(item){ item.classList.add('in-db'); item.innerHTML=item.innerHTML.replace(/<button.*<\/button>/,'<span class="cat-added">已加入</span>'); }
  await loadMyStocks();
  showChart(ticker);
}

// ── Search dropdown ───────────────────────────────────────────
const searchInput = document.getElementById('searchInput');
const dropdown = document.getElementById('dropdown');

searchInput.addEventListener('input', ()=>{
  clearTimeout(searchDebounce);
  searchDebounce = setTimeout(doSearch, 220);
});
searchInput.addEventListener('keydown', e=>{
  if(e.key==='Escape'){dropdown.style.display='none'; searchInput.blur();}
});
document.addEventListener('click', e=>{
  if(!e.target.closest('.search-wrap')) dropdown.style.display='none';
});

async function doSearch(){
  const q = searchInput.value.trim();
  if(q.length < 1){ dropdown.style.display='none'; return; }
  const ex = currentExchange === 'ALL' ? '' : currentExchange;
  const res = await fetch(`/api/catalog?q=${encodeURIComponent(q)}&exchange=${ex}`);
  const items = await res.json();
  if(!items.length){ dropdown.style.display='none'; return; }
  dropdown.innerHTML = items.slice(0,12).map(s=>`
    <div class="dd-item" onclick="pickSearch('${s.ticker}')">
      <div>
        <span style="font-weight:700;color:#e2e8f0">${s.ticker}</span>
        <span class="dd-in"> &nbsp;${s.name}</span>
      </div>
      <span class="dd-ex ${s.exchange}">${s.exchange}</span>
    </div>`).join('');
  dropdown.style.display = 'block';
}

async function pickSearch(ticker){
  dropdown.style.display='none';
  searchInput.value='';
  const inDb = await isInDb(ticker);
  if(!inDb){
    toast('載入中...');
    const res = await fetch('/api/stocks',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ticker})});
    const d = await res.json();
    if(!res.ok){toast('Error: '+d.error);return;}
    toast(`已加入 ${d.name}`);
    await loadMyStocks();
  }
  showChart(ticker);
}

async function isInDb(ticker){
  const res = await fetch(`/api/stocks/${ticker}`);
  return res.ok;
}

// ── Popular stocks ────────────────────────────────────────────
async function loadPopular(){
  const res = await fetch('/api/popular');
  const stocks = await res.json();
  const grid = document.getElementById('popularGrid');
  if(!stocks.length){ grid.innerHTML='<div class="empty-msg">無法載入熱門股票</div>'; return; }
  grid.innerHTML = stocks.map(s=>cardHTML(s)).join('');
}

// ── My stocks ─────────────────────────────────────────────────
async function loadMyStocks(){
  const res = await fetch('/api/stocks');
  let stocks = await res.json();
  const popular = ["AAPL","MSFT","NVDA","TSLA","AMZN"];
  // Exclude popular tickers from "my stocks"
  stocks = stocks.filter(s => !popular.includes(s.ticker));
  if(currentExchange !== 'ALL') stocks = stocks.filter(s=>s.exchange===currentExchange);
  const grid = document.getElementById('myGrid');
  if(!stocks.length){
    grid.innerHTML='<div class="empty-msg">尚無自訂股票。從搜尋或目錄新增。</div>';
    return;
  }
  grid.innerHTML = stocks.map(s=>cardHTML(s)).join('');
}

// ── Card HTML ─────────────────────────────────────────────────
function cardHTML(s){
  const k = s.kpis||{};
  const ex = s.exchange||'';
  const isActive = s.ticker===currentTicker;
  const mc = fmtCap(s.market_cap);
  const dt = s.last_updated ? new Date(s.last_updated).toLocaleDateString('zh-TW') : '';
  return `
  <div class="stock-card${isActive?' active':''}" id="card-${s.ticker}" onclick="showChart('${s.ticker}')">
    <div class="card-top">
      <div>
        <div class="card-ticker">${s.ticker}</div>
        <div class="card-name">${s.name||''}</div>
        <span class="ex-badge ${ex}">${ex}</span>
      </div>
      <div class="card-price">
        <div class="price">${s.current_price!=null?'$'+s.current_price.toFixed(2):'—'}</div>
        <div style="font-size:.68rem;color:var(--dim);margin-top:3px">市值 ${mc}</div>
      </div>
    </div>
    <div class="kpi-row">
      <div class="kpi"><div class="v" style="color:var(--green)">${fmt(k.latest_ocf)}</div><div class="l">OCF</div></div>
      <div class="kpi"><div class="v" style="color:var(--blue)">${fmt(k.latest_fcf)}</div><div class="l">FCF</div></div>
      <div class="kpi"><div class="v" style="color:var(--orange)">${k.ocf_cagr!=null?k.ocf_cagr.toFixed(1)+'%':'N/A'}</div><div class="l">CAGR</div></div>
      <div class="kpi"><div class="v" style="color:var(--purple)">${k.fcf_conversion!=null?k.fcf_conversion.toFixed(0)+'%':'N/A'}</div><div class="l">FCF Conv.</div></div>
      <div class="kpi"><div class="v" style="color:#f9a8d4">${k.pe_ratio!=null?k.pe_ratio.toFixed(1):'N/A'}</div><div class="l">P/E</div></div>
    </div>
    <div class="card-footer">
      <button class="btn btn-refresh" onclick="event.stopPropagation();refreshCard('${s.ticker}')">&#8635; 更新</button>
      <button class="btn btn-del" onclick="event.stopPropagation();deleteCard('${s.ticker}')">&#10005;</button>
      <span class="updated">${dt}</span>
    </div>
  </div>`;
}

// ── View switcher (現金流 / 趨勢) ─────────────────────────────
function setView(v){
  currentView = v;
  document.getElementById('tabCF').classList.toggle('active',    v==='cf');
  document.getElementById('tabTrend').classList.toggle('active', v==='trend');
  document.getElementById('cf-section').style.display    = v==='cf'    ? 'block' : 'none';
  document.getElementById('trend-section').style.display = v==='trend' ? 'block' : 'none';
  // Show period toggle only in CF view
  const toggle = document.getElementById('periodToggle');
  if(v==='cf') toggle.style.display = currentStockData?.has_quarterly ? 'flex' : 'none';
  else toggle.style.display = 'none';
  if(v==='trend') loadTrend(currentTicker, currentRange);
}

// ── Show chart ────────────────────────────────────────────────
async function showChart(ticker){
  currentTicker = ticker;
  currentPeriod = 'annual';
  currentView   = 'cf';
  document.querySelectorAll('.stock-card').forEach(c=>c.classList.remove('active'));
  ['card-'+ticker].forEach(id=>{const e=document.getElementById(id);if(e)e.classList.add('active');});

  const res = await fetch(`/api/stocks/${ticker}`);
  if(!res.ok){toast('找不到資料');return;}
  currentStockData = await res.json();

  document.getElementById('chart-panel').style.display='block';
  document.getElementById('chart-title').textContent=`${currentStockData.name} (${ticker})`;

  // Detect whether CF data exists
  const hasCF = currentStockData.annual &&
                Array.isArray(currentStockData.annual.labels) &&
                currentStockData.annual.labels.length > 0;

  // Show/hide CF tab
  document.getElementById('tabCF').style.display = hasCF ? '' : 'none';

  // Period toggle visibility
  const toggle = document.getElementById('periodToggle');

  if(hasCF){
    currentView = 'cf';
    document.getElementById('cf-section').style.display    = 'block';
    document.getElementById('trend-section').style.display = 'none';
    document.getElementById('tabCF').classList.add('active');
    document.getElementById('tabTrend').classList.remove('active');
    toggle.style.display = currentStockData.has_quarterly ? 'flex' : 'none';
    document.getElementById('btnAnnual').classList.add('active');
    document.getElementById('btnQuarterly').classList.remove('active');
    renderChart('annual');
  } else {
    currentView = 'trend';
    document.getElementById('cf-section').style.display    = 'none';
    document.getElementById('trend-section').style.display = 'block';
    document.getElementById('tabCF').classList.remove('active');
    document.getElementById('tabTrend').classList.add('active');
    toggle.style.display = 'none';
    loadTrend(ticker, currentRange);
  }

  document.getElementById('chart-panel').scrollIntoView({behavior:'smooth'});
}

function setPeriod(p){
  currentPeriod = p;
  document.getElementById('btnAnnual').classList.toggle('active', p==='annual');
  document.getElementById('btnQuarterly').classList.toggle('active', p==='quarterly');
  renderChart(p);
}

function renderChart(period){
  const s = currentStockData;
  const series = period==='quarterly' ? s.quarterly : s.annual;
  if(!series){toast('無季度資料');return;}

  // KPIs (annual always)
  const k = s.kpis||{};
  document.getElementById('kpiCards').innerHTML=`
    <div class="kpi-card"><div class="v" style="color:var(--green)">${fmt(k.latest_ocf)}</div><div class="l">最新 OCF</div><div class="s">營業現金流</div></div>
    <div class="kpi-card"><div class="v" style="color:var(--blue)">${fmt(k.latest_fcf)}</div><div class="l">最新 FCF</div><div class="s">自由現金流</div></div>
    <div class="kpi-card"><div class="v" style="color:var(--orange)">${k.ocf_cagr!=null?k.ocf_cagr.toFixed(1)+'%':'N/A'}</div><div class="l">OCF CAGR</div><div class="s">年複合成長</div></div>
    <div class="kpi-card"><div class="v" style="color:var(--purple)">${k.fcf_conversion!=null?k.fcf_conversion.toFixed(0)+'%':'N/A'}</div><div class="l">FCF 轉換率</div><div class="s">FCF / OCF</div></div>`;

  // Table
  const rows = series.labels.map((lbl,i)=>{
    const o=series.ocf[i], prev=i>0?series.ocf[i-1]:null;
    let yoy='–';
    if(o!=null&&prev!=null&&prev!==0){
      const p=((o-prev)/Math.abs(prev)*100).toFixed(1);
      const col=p>=0?'var(--green)':'var(--red)';
      yoy=`<span style="color:${col}">${p>=0?'+':''}${p}%</span>`;
    }
    const conv=(series.fcf[i]!=null&&series.ocf[i])?(series.fcf[i]/series.ocf[i]*100).toFixed(0)+'%':'N/A';
    return `<tr>
      <td>${lbl}</td>
      <td style="color:var(--green)">${fmt(series.ocf[i])}</td>
      <td>${yoy}</td>
      <td style="color:var(--red)">${fmt(series.capex[i])}</td>
      <td style="color:var(--orange)">${fmt(series.interest[i])}</td>
      <td style="color:var(--blue)">${fmt(series.fcf[i])}</td>
      <td style="color:var(--purple)">${conv}</td>
    </tr>`;
  }).join('');
  document.getElementById('chartTable').innerHTML=rows;

  // Chart
  if(cfChart) cfChart.destroy();
  const ctx = document.getElementById('cfChart').getContext('2d');
  cfChart = new Chart(ctx,{
    type:'bar',
    data:{
      labels: series.labels,
      datasets:[
        {label:'營業現金流 (OCF)',data:series.ocf,backgroundColor:'rgba(74,222,128,.72)',borderColor:'rgba(74,222,128,1)',borderWidth:1,borderRadius:3,yAxisID:'y'},
        {label:'資本支出 (CapEx)',data:series.capex,backgroundColor:'rgba(248,113,113,.72)',borderColor:'rgba(248,113,113,1)',borderWidth:1,borderRadius:3,yAxisID:'y'},
        {label:'利息費用',data:series.interest,backgroundColor:'rgba(251,191,36,.72)',borderColor:'rgba(251,191,36,1)',borderWidth:1,borderRadius:3,yAxisID:'y'},
        {label:'自由現金流 (FCF)',data:series.fcf,type:'line',borderColor:'rgba(96,165,250,1)',backgroundColor:'rgba(96,165,250,.12)',borderWidth:2.5,pointRadius:4,pointHoverRadius:7,fill:true,tension:.3,yAxisID:'y',datalabels:{display:false}},
      ],
    },
    options:{
      responsive:true,maintainAspectRatio:false,
      interaction:{mode:'index',intersect:false},
      plugins:{
        legend:{position:'bottom',labels:{color:'#cdd6f4',usePointStyle:true,padding:18}},
        tooltip:{backgroundColor:'#0f3460',titleColor:'#e2e8f0',bodyColor:'#94a3b8',
          callbacks:{label:c=>{const v=c.parsed.y;return v==null?`${c.dataset.label}: N/A`:` ${c.dataset.label}: ${fmt(v)}`;}}
        },
        datalabels:{
          display:c=>c.datasetIndex===0&&(series.labels.length<=6||c.dataIndex%2===0),
          color:'#4ade80',anchor:'end',align:'top',font:{size:9,weight:'bold'},
          formatter:v=>v?fmt(v):'',
        },
      },
      scales:{
        x:{ticks:{color:'#94a3b8',font:{size:10}},grid:{color:'rgba(255,255,255,0.04)'}},
        y:{ticks:{color:'#94a3b8',callback:v=>Math.abs(v)>=1000?`$${(v/1000).toFixed(0)}B`:`$${v}M`},grid:{color:'rgba(255,255,255,0.06)'}},
      },
    },
  });
}

// ── Range selector (trend) ────────────────────────────────────
function setRange(btn){
  document.querySelectorAll('.range-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  currentRange = btn.dataset.p;
  loadTrend(currentTicker, currentRange);
}

// ── Load & render trend chart ─────────────────────────────────
async function loadTrend(ticker, period){
  if(!ticker) return;
  const res = await fetch(`/api/stocks/${ticker}/history?period=${period}`);
  if(!res.ok){ toast('無法取得價格資料'); return; }
  const d = await res.json();
  renderTrend(d);
}

function renderTrend(d){
  const st = d.stats || {};
  const chgColor = (st.pct_change >= 0) ? 'var(--green)' : 'var(--red)';
  const chgSign  = (st.pct_change >= 0) ? '+' : '';

  // Stats cards
  document.getElementById('trendStats').innerHTML = `
    <div class="stat-card">
      <div class="v" style="color:var(--green)">$${st.latest_price?.toFixed(2) ?? 'N/A'}</div>
      <div class="l">目前價格</div>
    </div>
    <div class="stat-card">
      <div class="v" style="color:${chgColor}">${st.pct_change!=null ? chgSign+st.pct_change.toFixed(2)+'%' : 'N/A'}</div>
      <div class="l">區間漲跌幅</div>
    </div>
    <div class="stat-card">
      <div class="v" style="color:#e2e8f0">$${st.high_52w?.toFixed(2) ?? 'N/A'}</div>
      <div class="l">區間最高</div>
    </div>
    <div class="stat-card">
      <div class="v" style="color:#e2e8f0">$${st.low_52w?.toFixed(2) ?? 'N/A'}</div>
      <div class="l">區間最低</div>
    </div>
    <div class="stat-card">
      <div class="v" style="color:var(--purple)">${st.pe_ratio?.toFixed(1) ?? 'N/A'}</div>
      <div class="l">P/E 本益比</div>
    </div>`;

  // Update MA legend
  const [maA, maB] = d.ma_labels ?? ['MA20','MA50'];
  document.getElementById('maLegend').innerHTML =
    `<span style="color:#60a5fa">&#9644;</span> 收盤價 &nbsp;` +
    `<span style="color:#fbbf24">&#9644;</span> ${maA} &nbsp;` +
    `<span style="color:#f87171">&#9644;</span> ${maB}`;

  // Thin date labels (for 1D show HH:MM as-is, else trim to MM-DD)
  const is1D = d.period === '1d';
  const skip = Math.max(1, Math.floor(d.dates.length / 8));
  const labels = d.dates.map((dt, i) => i % skip === 0 ? (is1D ? dt : dt.slice(5)) : '');

  // Gradient fill
  const makeGrad = (ctx, color) => {
    const g = ctx.createLinearGradient(0,0,0,320);
    g.addColorStop(0, color.replace('1)', '.35)'));
    g.addColorStop(1, color.replace('1)', '0)'));
    return g;
  };

  // Price chart
  if(trendChart) trendChart.destroy();
  const tCtx = document.getElementById('trendChart').getContext('2d');
  trendChart = new Chart(tCtx, {
    type: 'line',
    data: {
      labels: d.dates,
      datasets: [
        {
          label: '收盤價',
          data: d.close,
          borderColor: 'rgba(96,165,250,1)',
          backgroundColor: makeGrad(tCtx, 'rgba(96,165,250,1)'),
          borderWidth: 1.8,
          pointRadius: 0,
          pointHoverRadius: 5,
          fill: true,
          tension: 0.2,
          yAxisID: 'y',
        },
        {
          label: d.ma_labels?.[0] ?? 'MA20',
          data: d.ma20,
          borderColor: 'rgba(251,191,36,0.85)',
          borderWidth: 1.3,
          borderDash: [4,3],
          pointRadius: 0,
          fill: false,
          tension: 0.2,
          yAxisID: 'y',
        },
        {
          label: d.ma_labels?.[1] ?? 'MA50',
          data: d.ma50,
          borderColor: 'rgba(248,113,113,0.85)',
          borderWidth: 1.3,
          borderDash: [6,4],
          pointRadius: 0,
          fill: false,
          tension: 0.2,
          yAxisID: 'y',
        },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'bottom', labels: { color: '#cdd6f4', usePointStyle: true, padding: 16, font: {size:11} }},
        tooltip: {
          backgroundColor: '#0f3460', titleColor: '#e2e8f0', bodyColor: '#94a3b8',
          callbacks: { title: items => items[0].label, label: c => ` ${c.dataset.label}: $${c.parsed.y?.toFixed(2) ?? 'N/A'}` }
        },
        datalabels: { display: false },
      },
      scales: {
        x: {
          ticks: { color:'#94a3b8', font:{size:10}, maxRotation:0,
            callback: (val, i) => i % skip === 0 ? d.dates[i].slice(5) : '' },
          grid: { color: 'rgba(255,255,255,0.04)' },
        },
        y: {
          ticks: { color:'#94a3b8', font:{size:10}, callback: v => '$'+v.toFixed(0) },
          grid: { color: 'rgba(255,255,255,0.06)' },
        },
      },
    },
  });

  // Volume chart
  if(volChart) volChart.destroy();
  const vCtx = document.getElementById('volChart').getContext('2d');
  const latest = d.close;
  const volColors = d.volume.map((_, i) =>
    i === 0 ? 'rgba(96,165,250,0.5)' :
    latest[i] >= latest[i-1] ? 'rgba(74,222,128,0.55)' : 'rgba(248,113,113,0.55)'
  );
  volChart = new Chart(vCtx, {
    type: 'bar',
    data: {
      labels: d.dates,
      datasets: [{
        label: '成交量',
        data: d.volume,
        backgroundColor: volColors,
        borderWidth: 0,
        borderRadius: 1,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#0f3460', titleColor: '#e2e8f0', bodyColor: '#94a3b8',
          callbacks: {
            title: items => items[0].label,
            label: c => ` 成交量: ${(c.parsed.y/1e6).toFixed(1)}M` ,
          }
        },
        datalabels: { display: false },
      },
      scales: {
        x: {
          ticks: { color:'#94a3b8', font:{size:9}, maxRotation:0,
            callback: (val, i) => i % skip === 0 ? d.dates[i].slice(5) : '' },
          grid: { display: false },
        },
        y: {
          ticks: { color:'#94a3b8', font:{size:9}, callback: v => (v/1e6).toFixed(0)+'M' },
          grid: { color: 'rgba(255,255,255,0.04)' },
        },
      },
    },
  });
}

// ── CRUD helpers ──────────────────────────────────────────────
async function refreshCard(ticker){
  toast('更新中...');
  const res=await fetch(`/api/stocks/${ticker}/refresh`,{method:'POST'});
  const d=await res.json();
  if(!res.ok){toast('Error: '+d.error);return;}
  toast(`${ticker} 已更新`);
  await loadMyStocks();
  await loadPopular();
  if(currentTicker===ticker) showChart(ticker);
}

async function deleteCard(ticker){
  if(!confirm(`確定移除 ${ticker}？`)) return;
  await fetch(`/api/stocks/${ticker}`,{method:'DELETE'});
  if(currentTicker===ticker){
    currentTicker=null;
    document.getElementById('chart-panel').style.display='none';
  }
  toast(`已移除 ${ticker}`);
  loadMyStocks();
  loadPopular();
  if(catalogVisible) loadCatalog();
}

// ── Init ──────────────────────────────────────────────────────
(async function(){
  await loadPopular();
  await loadMyStocks();
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    import os, pathlib
    pid_file = pathlib.Path(__file__).parent / ".server.pid"
    pid_file.write_text(str(os.getpid()))
    print("Finance Dashboard v2 starting...")
    print("  URL: http://localhost:5000")
    print("  MongoDB: mongodb://localhost:27017/finance_dashboard")
    try:
        app.run(host="0.0.0.0", port=5000, debug=False)
    finally:
        pid_file.unlink(missing_ok=True)
