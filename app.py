"""
Finance Dashboard v2
Flask + MongoDB + yfinance
NYSE / NASDAQ / AMEX  |  Annual & Quarterly  |  Popular stocks on load
"""

from flask import Flask, jsonify, request, render_template_string, Response, stream_with_context
import json
from pymongo import MongoClient
from datetime import datetime, timezone
import yfinance as yf
import math

app = Flask(__name__)
import os as _os
client = MongoClient(_os.environ.get("MONGO_URI", "mongodb://localhost:27017/"))
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
    docs = list(stocks_col.find({"pinned": {"$ne": False}}, {"_id": 0,
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
    stocks_col.update_one({"ticker": ticker}, {"$set": {**data, "pinned": True}}, upsert=True)
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


@app.route("/api/stocks", methods=["DELETE"])
def clear_my_stocks():
    """Delete all non-popular stocks from MongoDB."""
    popular = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"]
    r = stocks_col.delete_many({"ticker": {"$nin": popular}, "pinned": {"$ne": False}})
    return jsonify({"ok": True, "deleted": r.deleted_count})


@app.route("/api/stocks/<ticker>", methods=["DELETE"])
def delete_stock(ticker):
    r = stocks_col.delete_one({"ticker": ticker.upper()})
    return (jsonify({"ok": True}) if r.deleted_count else jsonify({"error": "not found"}), 404)


@app.route("/api/stocks/<ticker>/history")
def stock_history(ticker):
    """Price history + volume + MA20 + MA50 for trend chart."""
    period   = request.args.get("period", "1y")   # 1d 1mo 3mo 6mo 1y 2y 5y
    # Serve from MongoDB cache when available (skip 1d — always live)
    if period != "1d" and request.args.get("refresh") != "1":
        cache_field = f"history_cache_{period}"
        doc = stocks_col.find_one({"ticker": ticker.upper()}, {cache_field: 1, "_id": 0})
        if doc and doc.get(cache_field):
            return jsonify(doc[cache_field])
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


@app.route("/api/compare")
def compare_stocks():
    """Normalized % change for multiple tickers (comparison overlay)."""
    tickers_raw = request.args.get("tickers", "")
    period = request.args.get("period", "1y")
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()][:8]
    if not tickers:
        return jsonify({"error": "no tickers"}), 400
    if period == "1d":
        interval = "5m"
    elif period in ("1mo", "3mo", "6mo", "1y"):
        interval = "1d"
    else:
        interval = "1wk"
    result = {}
    common_dates = None
    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(period=period, interval=interval)
            if hist.empty:
                continue
            closes = hist["Close"].round(2).tolist()
            if period == "1d":
                dates = [d.strftime("%H:%M") for d in hist.index]
            else:
                dates = [d.strftime("%Y-%m-%d") for d in hist.index]
            if common_dates is None:
                common_dates = dates
            first = closes[0] if closes else None
            normalized = [round((c - first) / first * 100, 2) for c in closes] if first else closes
            result[ticker] = {"dates": dates, "close": closes, "normalized": normalized}
        except Exception:
            pass
    return jsonify({"period": period, "interval": interval, "dates": common_dates or [], "tickers": result})


@app.route("/api/stocks/<ticker>/pin", methods=["POST"])
def pin_stock(ticker):
    """Mark a stock as pinned so it appears in My Stocks."""
    stocks_col.update_one({"ticker": ticker.upper()}, {"$set": {"pinned": True}})
    return jsonify({"ok": True})


@app.route("/api/stocks/<ticker>/refresh", methods=["POST"])
def refresh_stock(ticker):
    try:
        data = fetch_stock(ticker.upper())
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    stocks_col.update_one({"ticker": ticker.upper()}, {"$set": data}, upsert=True)
    return jsonify({"ok": True, "name": data["name"]})


@app.route("/api/sectors")
def sectors():
    """Return unique sectors from the stocks collection."""
    result = stocks_col.distinct("sector")
    return jsonify(sorted([s for s in result if s]))


@app.route("/api/screener")
def screener():
    """Full-catalog screener: all 307 tickers when no KPI filter; DB-only when filters set."""
    ex           = request.args.get("exchange", "")
    sector       = request.args.get("sector", "")
    min_cagr     = request.args.get("min_cagr",     type=float)
    max_cagr     = request.args.get("max_cagr",     type=float)
    min_fcf_conv = request.args.get("min_fcf_conv", type=float)
    max_fcf_conv = request.args.get("max_fcf_conv", type=float)
    min_pe       = request.args.get("min_pe",       type=float)
    max_pe       = request.args.get("max_pe",       type=float)

    has_kpi_filter = any(v is not None for v in
                         [min_cagr, max_cagr, min_fcf_conv, max_fcf_conv, min_pe, max_pe])

    # Build DB query (always restrict by exchange/sector/KPI as applicable)
    db_query = {}
    if ex and ex != "ALL":
        db_query["exchange"] = ex
    if sector:
        db_query["sector"] = sector
    if has_kpi_filter:
        if min_cagr     is not None: db_query.setdefault("kpis.ocf_cagr",      {})["$gte"] = min_cagr
        if max_cagr     is not None: db_query.setdefault("kpis.ocf_cagr",      {})["$lte"] = max_cagr
        if min_fcf_conv is not None: db_query.setdefault("kpis.fcf_conversion",{})["$gte"] = min_fcf_conv
        if max_fcf_conv is not None: db_query.setdefault("kpis.fcf_conversion",{})["$lte"] = max_fcf_conv
        if min_pe       is not None: db_query.setdefault("kpis.pe_ratio",       {})["$gte"] = min_pe
        if max_pe       is not None: db_query.setdefault("kpis.pe_ratio",       {})["$lte"] = max_pe

    db_map = {d["ticker"]: d for d in stocks_col.find(db_query, {
        "_id": 0, "ticker": 1, "name": 1, "exchange": 1, "sector": 1,
        "current_price": 1, "market_cap": 1, "kpis": 1,
    })}

    if has_kpi_filter or sector:
        # KPI/sector filters require DB data — return only matching DB rows
        result = sorted(db_map.values(), key=lambda x: x["ticker"])
    else:
        # No KPI filter — show full catalog, merge DB data where available
        cat_query = {}
        if ex and ex != "ALL":
            cat_query["exchange"] = ex
        cat_docs = sorted(catalog_col.find(cat_query, {"_id": 0}),
                          key=lambda x: x["ticker"])
        result = []
        for c in cat_docs:
            if c["ticker"] in db_map:
                result.append(db_map[c["ticker"]])
            else:
                result.append({
                    "ticker": c["ticker"], "name": c["name"],
                    "exchange": c["exchange"], "in_db": False,
                })

    return jsonify(result)


@app.route("/api/stocks/<ticker>/dividends")
def stock_dividends(ticker):
    """Dividend payment history from yfinance."""
    if request.args.get("refresh") != "1":
        doc = stocks_col.find_one({"ticker": ticker.upper()}, {"dividends_cache": 1, "_id": 0})
        if doc and doc.get("dividends_cache"):
            return jsonify(doc["dividends_cache"])
    try:
        t = yf.Ticker(ticker.upper())
        divs = t.dividends
        if divs is None or divs.empty:
            return jsonify({"has_dividends": False})

        dates   = [d.strftime("%Y-%m-%d") for d in divs.index]
        amounts = [round(float(v), 4) for v in divs.values]

        # Aggregate by calendar year
        annual_map = {}
        for d, a in zip(divs.index, divs.values):
            yr = str(d.year)
            annual_map[yr] = round(annual_map.get(yr, 0) + float(a), 4)
        ann_labels  = sorted(annual_map.keys())
        ann_amounts = [annual_map[y] for y in ann_labels]

        info = t.info
        div_yield  = safe(info.get("dividendYield"))
        trailing   = safe(info.get("trailingAnnualDividendRate"))

        return jsonify({
            "has_dividends": True,
            "dates":   dates,
            "amounts": amounts,
            "annual":  {"labels": ann_labels, "dividends": ann_amounts},
            "stats": {
                "trailing_annual": trailing,
                "yield_pct": round(div_yield, 2) if div_yield else None,
                "last_amount": amounts[-1] if amounts else None,
                "last_date":   dates[-1]   if dates   else None,
            },
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/stocks/<ticker>/financials")
def stock_financials(ticker):
    """Revenue, Net Income, EPS history from yfinance income statement."""
    if request.args.get("refresh") != "1":
        doc = stocks_col.find_one({"ticker": ticker.upper()}, {"financials_cache": 1, "_id": 0})
        if doc and doc.get("financials_cache"):
            return jsonify(doc["financials_cache"])
    try:
        t = yf.Ticker(ticker.upper())

        def build_fin_series(income, quarterly=False):
            if income is None or income.empty:
                return None
            rev_k, _  = extract_series(income, income, ("total", "revenue"), ("revenue",))
            ni_k,  _  = extract_series(income, income, ("net", "income",))
            eps_k, _  = extract_series(income, income, ("diluted", "eps"), ("basic", "eps"), ("eps",))
            labels, rev_v, ni_v, eps_v = [], [], [], []
            for col in reversed(income.columns):
                if quarterly:
                    labels.append(f"Q{((col.month - 1) // 3) + 1}'{str(col.year)[2:]}")
                else:
                    labels.append(f"FY{col.year}")

                def get_val(key, c=col, divisor=1e6):
                    if key and key in income.index and c in income.columns:
                        v = safe(income.loc[key, c])
                        return round(v / divisor, 2) if v is not None else None
                    return None

                rev_v.append(get_val(rev_k))
                ni_v.append(get_val(ni_k))
                eps_v.append(get_val(eps_k, divisor=1))
            return {"labels": labels, "revenue": rev_v, "net_income": ni_v, "eps": eps_v}

        annual   = build_fin_series(t.income_stmt)
        qinc     = t.quarterly_income_stmt
        quarterly = build_fin_series(qinc, quarterly=True) if qinc is not None and not qinc.empty else None

        if annual is None:
            return jsonify({"has_financials": False})

        rev_valid = [v for v in annual["revenue"]    if v is not None and v > 0]
        eps_valid = [v for v in annual["eps"]        if v is not None]
        ni_valid  = [v for v in annual["net_income"] if v is not None]
        latest_rev = rev_valid[-1] if rev_valid else None
        latest_eps = eps_valid[-1] if eps_valid else None
        latest_ni  = ni_valid[-1]  if ni_valid  else None
        rev_cagr   = None
        if len(rev_valid) >= 2:
            n = len(rev_valid) - 1
            try:
                rev_cagr = round(((rev_valid[-1] / rev_valid[0]) ** (1 / n) - 1) * 100, 2)
            except Exception:
                pass

        return jsonify({
            "has_financials": True,
            "has_quarterly":  quarterly is not None,
            "annual":    annual,
            "quarterly": quarterly,
            "kpis": {
                "latest_rev": latest_rev,
                "rev_cagr":   rev_cagr,
                "latest_eps": latest_eps,
                "latest_ni":  latest_ni,
            },
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/prices/stream")
def price_stream():
    """SSE: push live prices every 30s for all tracked stocks."""
    import time as _time
    def generate():
        while True:
            try:
                tickers = [d["ticker"] for d in stocks_col.find(
                    {"pinned": {"$ne": False}}, {"ticker": 1, "_id": 0}
                )]
                updates = []
                for t in tickers:
                    try:
                        fi = yf.Ticker(t).fast_info
                        price = getattr(fi, "last_price", None)
                        prev  = getattr(fi, "previous_close", None)
                        if price is None:
                            continue
                        price = float(price)
                        chg   = round((price - float(prev)) / float(prev) * 100, 2) if prev else None
                        updates.append({"ticker": t, "price": round(price, 2), "change_pct": chg})
                    except Exception:
                        pass
                yield f"data: {json.dumps(updates)}\n\n"
            except Exception:
                yield "data: []\n\n"
            _time.sleep(30)
    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Historical-data helpers (used by both live endpoints and backup) ──────────

def _fetch_dividends_payload(ticker_str):
    """Fetch dividend history from yfinance and return serialisable dict."""
    t    = yf.Ticker(ticker_str)
    divs = t.dividends
    if divs is None or divs.empty:
        return {"has_dividends": False}
    dates   = [d.strftime("%Y-%m-%d") for d in divs.index]
    amounts = [round(float(v), 4)     for v in divs.values]
    annual_map = {}
    for d, a in zip(divs.index, divs.values):
        yr = str(d.year)
        annual_map[yr] = round(annual_map.get(yr, 0) + float(a), 4)
    ann_labels  = sorted(annual_map.keys())
    ann_amounts = [annual_map[y] for y in ann_labels]
    info      = t.info
    div_yield = safe(info.get("dividendYield"))
    trailing  = safe(info.get("trailingAnnualDividendRate"))
    return {
        "has_dividends": True,
        "dates":   dates,
        "amounts": amounts,
        "annual":  {"labels": ann_labels, "dividends": ann_amounts},
        "stats": {
            "trailing_annual": trailing,
            "yield_pct":   round(div_yield, 2) if div_yield else None,
            "last_amount": amounts[-1] if amounts else None,
            "last_date":   dates[-1]   if dates   else None,
        },
    }


def _fetch_financials_payload(ticker_str):
    """Fetch income-statement history from yfinance and return serialisable dict."""
    t = yf.Ticker(ticker_str)

    def build_fin_series(income, quarterly=False):
        if income is None or income.empty:
            return None
        rev_k, _ = extract_series(income, income, ("total", "revenue"), ("revenue",))
        ni_k,  _ = extract_series(income, income, ("net", "income",))
        eps_k, _ = extract_series(income, income, ("diluted", "eps"), ("basic", "eps"), ("eps",))
        labels, rev_v, ni_v, eps_v = [], [], [], []
        for col in reversed(income.columns):
            labels.append(f"Q{((col.month-1)//3)+1}'{str(col.year)[2:]}" if quarterly else f"FY{col.year}")
            def get_val(key, c=col, divisor=1e6):
                if key and key in income.index and c in income.columns:
                    v = safe(income.loc[key, c])
                    return round(v / divisor, 2) if v is not None else None
                return None
            rev_v.append(get_val(rev_k))
            ni_v.append(get_val(ni_k))
            eps_v.append(get_val(eps_k, divisor=1))
        return {"labels": labels, "revenue": rev_v, "net_income": ni_v, "eps": eps_v}

    annual   = build_fin_series(t.income_stmt)
    qinc     = t.quarterly_income_stmt
    quarterly = build_fin_series(qinc, quarterly=True) if qinc is not None and not qinc.empty else None
    if annual is None:
        return {"has_financials": False}
    rev_valid = [v for v in annual["revenue"]    if v is not None and v > 0]
    eps_valid = [v for v in annual["eps"]        if v is not None]
    ni_valid  = [v for v in annual["net_income"] if v is not None]
    latest_rev = rev_valid[-1] if rev_valid else None
    latest_eps = eps_valid[-1] if eps_valid else None
    latest_ni  = ni_valid[-1]  if ni_valid  else None
    rev_cagr   = None
    if len(rev_valid) >= 2:
        n = len(rev_valid) - 1
        try:
            rev_cagr = round(((rev_valid[-1] / rev_valid[0]) ** (1 / n) - 1) * 100, 2)
        except Exception:
            pass
    return {
        "has_financials": True,
        "has_quarterly":  quarterly is not None,
        "annual":    annual,
        "quarterly": quarterly,
        "kpis": {"latest_rev": latest_rev, "rev_cagr": rev_cagr,
                 "latest_eps": latest_eps, "latest_ni": latest_ni},
    }


def _fetch_history_payload(ticker_str, period):
    """Fetch OHLCV + MA price history from yfinance (skip 1d — too ephemeral)."""
    if period == "1d":
        return None
    interval = "1d" if period in ("1mo","3mo","6mo","1y") else "1wk"
    hist = yf.Ticker(ticker_str).history(period=period, interval=interval)
    if hist.empty:
        return None
    closes  = hist["Close"].round(2).tolist()
    volumes = hist["Volume"].tolist()
    highs   = hist["High"].round(2).tolist()
    lows    = hist["Low"].round(2).tolist()
    dates   = [d.strftime("%Y-%m-%d") for d in hist.index]
    def ma(n):
        out = []
        for i in range(len(closes)):
            out.append(None if i < n-1 else round(sum(closes[i-n+1:i+1]) / n, 2))
        return out
    c_latest = closes[-1] if closes else None
    c_first  = closes[0]  if closes else None
    pct_chg  = round((c_latest - c_first) / c_first * 100, 2) if c_first else None
    db_doc   = stocks_col.find_one({"ticker": ticker_str}, {"kpis.pe_ratio": 1, "_id": 0})
    pe       = db_doc.get("kpis", {}).get("pe_ratio") if db_doc else None
    return {
        "ticker": ticker_str, "period": period, "interval": interval,
        "dates": dates, "close": closes, "volume": volumes,
        "ma20": ma(20), "ma50": ma(50), "ma_labels": ["MA20","MA50"],
        "stats": {
            "latest_price": c_latest, "pct_change": pct_chg,
            "high_52w": round(max(h for h in highs if h), 2) if highs else None,
            "low_52w":  round(min(l for l in lows  if l), 2) if lows  else None,
            "pe_ratio": pe,
        },
    }


@app.route("/api/backup-history")
def backup_history():
    """SSE: fetch & persist dividends, financials, 1y+5y price history for all DB stocks."""
    import time as _time
    def generate():
        tickers = sorted(d["ticker"] for d in stocks_col.find({}, {"ticker": 1, "_id": 0}))
        total   = len(tickers)
        yield f"data: {json.dumps({'total': total, 'done': 0, 'ticker': ''})}\n\n"
        for i, ticker in enumerate(tickers):
            try:
                update = {"history_cache_at": datetime.now(timezone.utc).isoformat()}
                try:
                    update["dividends_cache"] = _fetch_dividends_payload(ticker)
                except Exception:
                    pass
                try:
                    update["financials_cache"] = _fetch_financials_payload(ticker)
                except Exception:
                    pass
                for p in ("1y", "5y"):
                    try:
                        h = _fetch_history_payload(ticker, p)
                        if h:
                            update[f"history_cache_{p}"] = h
                    except Exception:
                        pass
                stocks_col.update_one({"ticker": ticker}, {"$set": update})
                yield f"data: {json.dumps({'total': total, 'done': i+1, 'ticker': ticker})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'total': total, 'done': i+1, 'ticker': ticker, 'error': str(e)})}\n\n"
            _time.sleep(0.3)
        yield f"data: {json.dumps({'total': total, 'done': total, 'finished': True})}\n\n"
    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/bulk-fetch")
def bulk_fetch():
    """Stream bulk-fetch progress via SSE; fetches all catalog tickers not yet in DB."""
    def generate():
        all_tickers = sorted(c["ticker"] for c in catalog_col.find({}, {"ticker": 1, "_id": 0}))
        in_db       = {d["ticker"] for d in stocks_col.find({}, {"ticker": 1, "_id": 0})}
        to_fetch    = [t for t in all_tickers if t not in in_db]
        total       = len(to_fetch)
        yield f"data: {json.dumps({'total': total, 'done': 0, 'ticker': ''})}\n\n"
        for i, ticker in enumerate(to_fetch):
            try:
                data = fetch_stock(ticker)
                stocks_col.update_one(
                    {"ticker": ticker},
                    {"$set": data, "$setOnInsert": {"pinned": False}},
                    upsert=True,
                )
                status = "ok"
            except Exception:
                status = "error"
            yield f"data: {json.dumps({'total': total, 'done': i + 1, 'ticker': ticker, 'status': status})}\n\n"
        yield f"data: {json.dumps({'total': total, 'done': total, 'finished': True})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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
<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
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
.price-chg{font-size:.68rem;margin-top:1px;transition:color .4s}
@keyframes flash-up{0%,100%{background:transparent}40%{background:rgba(74,222,128,.28);border-radius:4px}}
@keyframes flash-dn{0%,100%{background:transparent}40%{background:rgba(248,113,113,.28);border-radius:4px}}
.price-up{animation:flash-up .7s ease}
.price-dn{animation:flash-dn .7s ease}
.live-dot{width:7px;height:7px;border-radius:50%;background:#4ade80;display:inline-block;margin-left:6px;vertical-align:middle;cursor:default}
.live-dot.active{animation:live-pulse 2.4s ease-in-out infinite}
@keyframes live-pulse{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(74,222,128,.5)}60%{opacity:.7;box-shadow:0 0 0 5px rgba(74,222,128,0)}}
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
.export-wrap{display:flex;gap:4px}
.export-btn{padding:5px 11px;border-radius:7px;border:1px solid var(--border);background:var(--panel);color:var(--muted);cursor:pointer;font-size:.78rem;font-weight:600;transition:.15s}
.export-btn:hover{background:var(--border);color:var(--text)}
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

/* ── Compare section ────────────────── */
#compare-section{display:none}
.cmp-chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px;align-items:center;min-height:30px}
.cmp-chip{display:inline-flex;align-items:center;gap:5px;padding:4px 11px;border-radius:20px;font-size:.78rem;font-weight:700;border:1.5px solid}
.cmp-chip .rm{background:none;border:none;cursor:pointer;color:inherit;padding:0 0 0 2px;font-size:.85rem;opacity:.65;line-height:1}
.cmp-chip .rm:hover{opacity:1}
.cmp-add-wrap{display:flex;gap:6px;margin-bottom:14px}
.cmp-input-wrap{position:relative;flex:0 0 220px}
.cmp-input-wrap input{width:100%;background:var(--panel);border:1px solid var(--border);color:var(--text);padding:6px 12px;border-radius:7px;font-size:.83rem;outline:none}
.cmp-input-wrap input:focus{border-color:var(--accent)}
#cmpDropdown{
  position:absolute;top:calc(100% + 4px);left:0;right:0;
  background:var(--card);border:1px solid var(--border);border-radius:8px;
  max-height:220px;overflow-y:auto;z-index:300;display:none
}
#cmpDropdown .dd-item{
  padding:9px 14px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;
  font-size:.84rem;border-bottom:1px solid var(--border);
}
#cmpDropdown .dd-item:hover{background:var(--panel)}
#cmpDropdown .dd-item:last-child{border-bottom:none}
.cmp-add-wrap button{padding:6px 14px;background:var(--accent);color:#fff;border:none;border-radius:7px;cursor:pointer;font-size:.8rem;font-weight:600}
.cmp-empty{padding:60px;text-align:center;color:var(--dim);font-size:.9rem}
.cmp-wrap{height:400px;position:relative;margin-bottom:18px}

/* ── Screener panel ─────────────────── */
#screener-panel{background:var(--card);border-radius:14px;padding:20px;margin-bottom:24px;display:none}
#screener-panel h3{font-size:.9rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:14px}
.scr-filters{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end;margin-bottom:16px}
.scr-field{display:flex;flex-direction:column;gap:4px}
.scr-field label{font-size:.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.scr-field input,.scr-field select{
  background:var(--panel);border:1px solid var(--border);color:var(--text);
  padding:6px 10px;border-radius:7px;font-size:.83rem;outline:none;width:128px
}
.scr-field select{width:160px}
.scr-field input:focus,.scr-field select:focus{border-color:var(--accent)}
.scr-run{padding:7px 20px;background:var(--accent);color:#fff;border:none;border-radius:7px;cursor:pointer;font-size:.83rem;font-weight:600}
.scr-count{font-size:.78rem;color:var(--muted);margin-bottom:10px}
.scr-wrap{overflow-x:auto;max-height:460px;overflow-y:auto}
.scr-wrap table{width:100%;border-collapse:collapse;font-size:.8rem}
.bulk-bar-wrap{display:none;margin-bottom:14px}
.bulk-bar-track{background:var(--panel);border-radius:6px;height:8px;overflow:hidden;margin-bottom:6px}
.bulk-bar-fill{height:100%;background:var(--accent);border-radius:6px;width:0%;transition:width .3s}
.bulk-status{font-size:.76rem;color:var(--muted)}

/* ── Toast ──────────────────────────── */
.toast{position:fixed;bottom:22px;right:22px;background:var(--card);border:1px solid var(--border);color:var(--text);padding:11px 18px;border-radius:9px;font-size:.83rem;z-index:999;opacity:0;transition:.3s;pointer-events:none;max-width:300px}
.toast.show{opacity:1}
.empty-msg{text-align:center;padding:40px;color:var(--dim);font-size:.9rem}
</style>
</head>
<body>

<header>
  <h1>Finance Dashboard<span class="live-dot" id="liveDot" title="即時報價：連線中"></span></h1>
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
  <div style="margin-left:auto;display:flex;gap:6px">
    <button class="ex-tab" style="background:#1e1a2e;border-color:#3d2d5a;color:#a78bfa" onclick="toggleScreener()">&#9783; 篩選器</button>
    <button class="ex-tab" style="background:#1a2e1a;border-color:#2d4a2d;color:#4ade80" onclick="toggleCatalog()">+ 瀏覽股票目錄</button>
  </div>
</div>

<main>
  <!-- Catalog browser -->
  <div id="catalog-panel">
    <h3 id="catalog-title">NYSE 股票目錄</h3>
    <div class="cat-grid" id="catGrid"></div>
  </div>

  <!-- Screener panel -->
  <div id="screener-panel">
    <h3>股票篩選器</h3>
    <div class="scr-filters">
      <div class="scr-field">
        <label>產業</label>
        <select id="scrSector"><option value="">全部產業</option></select>
      </div>
      <div class="scr-field">
        <label>最低 OCF CAGR (%)</label>
        <input id="scrMinCagr" type="number" step="0.1" placeholder="例：10">
      </div>
      <div class="scr-field">
        <label>最低 FCF 轉換率 (%)</label>
        <input id="scrMinFcfConv" type="number" step="1" placeholder="例：70">
      </div>
      <div class="scr-field">
        <label>P/E 下限</label>
        <input id="scrMinPe" type="number" step="0.1" placeholder="例：10">
      </div>
      <div class="scr-field">
        <label>P/E 上限</label>
        <input id="scrMaxPe" type="number" step="0.1" placeholder="例：50">
      </div>
      <button class="scr-run" onclick="runScreener()">篩選</button>
      <button class="scr-run" style="background:var(--panel);color:var(--muted);border:1px solid var(--border)" onclick="resetScreener()">清除</button>
      <button class="scr-run" id="btnBulk"   style="background:#1a2e1a;border:1px solid #2d4a2d;color:#4ade80"   onclick="startBulkFetch()">&#8987; 載入全部數據</button>
      <button class="scr-run" id="btnBackup" style="background:#1a1a2e;border:1px solid #2d2d5a;color:#818cf8" onclick="startBackupHistory()">&#128190; 備份歷史資料</button>
    </div>
    <div class="bulk-bar-wrap" id="bulkBarWrap">
      <div class="bulk-bar-track"><div class="bulk-bar-fill" id="bulkFill"></div></div>
      <div class="bulk-status" id="bulkStatus"></div>
    </div>
    <div class="scr-count" id="scrCount"></div>
    <div class="scr-wrap">
      <table>
        <thead>
          <tr>
            <th>代碼</th><th>公司名稱</th><th>交易所</th><th>產業</th>
            <th>股價</th><th>OCF CAGR</th><th>FCF 轉換率</th><th>P/E</th><th></th>
          </tr>
        </thead>
        <tbody id="scrBody"></tbody>
      </table>
    </div>
  </div>

  <!-- Chart panel -->
  <div id="chart-panel">
    <div class="chart-header">
      <h3 id="chart-title"></h3>
      <div class="period-toggle" id="periodToggle" style="display:none">
        <button class="period-btn active" id="btnAnnual" onclick="setPeriod('annual')">年度</button>
        <button class="period-btn" id="btnQuarterly" onclick="setPeriod('quarterly')">季度</button>
      </div>
      <div class="export-wrap">
        <button class="export-btn" onclick="exportData('csv')">↓ CSV</button>
        <button class="export-btn" onclick="exportData('xlsx')">↓ Excel</button>
      </div>
    </div>
    <!-- View switcher -->
    <div class="view-tabs">
      <button class="view-tab active" id="tabCF"      onclick="setView('cf')">現金流分析</button>
      <button class="view-tab"        id="tabTrend"   onclick="setView('trend')">價格趨勢</button>
      <button class="view-tab"        id="tabDiv"     onclick="setView('div')">股息歷史</button>
      <button class="view-tab"        id="tabRev"     onclick="setView('rev')">營收/EPS</button>
      <button class="view-tab"        id="tabCompare" onclick="setView('compare')">多股比較</button>
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

    <!-- Dividend view -->
    <div id="div-section" style="display:none">
      <div class="stat-row" id="divStats"></div>
      <div class="chart-wrap"><canvas id="divChart"></canvas></div>
      <div class="table-wrap" style="max-height:300px;overflow-y:auto;margin-top:12px">
        <table>
          <thead>
            <tr>
              <th>付息日期</th>
              <th style="color:#facc15">每股股息 ($)</th>
              <th>YoY%（年度）</th>
            </tr>
          </thead>
          <tbody id="divTable"></tbody>
        </table>
      </div>
    </div>

    <!-- Revenue / EPS view -->
    <div id="rev-section" style="display:none">
      <div class="stat-row" id="revStats"></div>
      <div class="range-row" id="revPeriodRow" style="margin-bottom:10px">
        <span style="font-size:.75rem;color:var(--muted);margin-right:4px">期間：</span>
        <button class="period-btn active" id="revBtnAnnual"    onclick="setRevPeriod('annual')">年度</button>
        <button class="period-btn"        id="revBtnQuarterly" onclick="setRevPeriod('quarterly')">季度</button>
      </div>
      <div class="chart-wrap"><canvas id="revChart"></canvas></div>
      <div class="table-wrap" style="max-height:300px;overflow-y:auto;margin-top:12px">
        <table>
          <thead>
            <tr>
              <th>期間</th>
              <th style="color:#60a5fa">總營收 ($M)</th>
              <th>YoY%</th>
              <th style="color:#4ade80">淨利 ($M)</th>
              <th style="color:#fb923c">稀釋 EPS ($)</th>
            </tr>
          </thead>
          <tbody id="revTable"></tbody>
        </table>
      </div>
    </div>

    <!-- Compare view -->
    <div id="compare-section">
      <div class="cmp-chips" id="cmpChips"></div>
      <div class="cmp-add-wrap">
        <div class="cmp-input-wrap">
          <input id="cmpInput" placeholder="輸入代碼或公司名稱..." maxlength="20"
                 autocomplete="off">
          <div id="cmpDropdown"></div>
        </div>
        <button onclick="addCmpTicker()">+ 加入</button>
      </div>
      <div class="range-row" id="cmpRangeRow">
        <span style="font-size:.75rem;color:var(--muted);margin-right:4px">區間：</span>
        <button class="range-btn" data-p="1d"  onclick="setCmpRange(this)">1D</button>
        <button class="range-btn" data-p="1mo" onclick="setCmpRange(this)">1M</button>
        <button class="range-btn" data-p="3mo" onclick="setCmpRange(this)">3M</button>
        <button class="range-btn" data-p="6mo" onclick="setCmpRange(this)">6M</button>
        <button class="range-btn active" data-p="1y" onclick="setCmpRange(this)">1Y</button>
        <button class="range-btn" data-p="2y"  onclick="setCmpRange(this)">2Y</button>
        <button class="range-btn" data-p="5y"  onclick="setCmpRange(this)">5Y</button>
      </div>
      <div class="cmp-wrap"><canvas id="cmpChart"></canvas></div>
    </div>
  </div>

  <!-- Popular stocks -->
  <section id="popularSection">
    <h2>熱門股票</h2>
    <div class="stock-grid" id="popularGrid"><div class="empty-msg"><span class="spinner-inline"></span> 載入中...</div></div>
  </section>

  <!-- My stocks -->
  <section id="mySection">
    <h2 style="display:flex;align-items:center;gap:12px">
      我的股票
      <button onclick="clearAllMyStocks()" style="font-size:.72rem;padding:4px 12px;background:transparent;border:1px solid #4b5563;border-radius:6px;color:#6b7280;cursor:pointer;font-weight:500" onmouseover="this.style.borderColor='#ef4444';this.style.color='#ef4444'" onmouseout="this.style.borderColor='#4b5563';this.style.color='#6b7280'">全部清除</button>
    </h2>
    <div class="stock-grid" id="myGrid"><div class="empty-msg">尚無自訂股票。從搜尋或目錄新增。</div></div>
  </section>
</main>
<div class="toast" id="toast"></div>

<script>
Chart.register(ChartDataLabels);

let cfChart    = null;
let trendChart = null;
let volChart   = null;
let cmpChart   = null;
let divChart   = null;
let revChart   = null;
let revPeriod  = 'annual';
let currentRevData  = null;
let currentDivData  = null;
let currentTrendData = null;
let currentTicker    = null;
let currentPeriod    = 'annual';
let currentView      = 'cf';
let currentRange     = '1y';
let cmpRange         = '1y';
let cmpTickers       = [];
let currentExchange  = 'ALL';
let currentStockData = null;
let catalogVisible   = false;
let searchDebounce   = null;
const CMP_COLORS = [
  'rgba(96,165,250,1)','rgba(74,222,128,1)','rgba(248,113,113,1)','rgba(251,191,36,1)',
  'rgba(167,139,250,1)','rgba(251,146,60,1)','rgba(34,211,238,1)','rgba(244,114,182,1)',
];

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
  if(screenerVisible) runScreener();
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
async function clearAllMyStocks(){
  const grid = document.getElementById('myGrid');
  const count = grid.querySelectorAll('.stock-card').length;
  if(!count){ toast('沒有可清除的股票'); return; }
  if(!confirm(`確定要清除全部 ${count} 檔自訂股票嗎？\n（熱門股票不受影響）`)) return;
  const res = await fetch('/api/stocks', {method:'DELETE'});
  const d = await res.json();
  toast(`已清除 ${d.deleted} 檔股票`);
  if(currentTicker && !["AAPL","MSFT","NVDA","TSLA","AMZN"].includes(currentTicker)){
    currentTicker = null;
    document.getElementById('chart-panel').style.display = 'none';
  }
  await loadMyStocks();
  if(screenerVisible) runScreener();
}

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
        <div class="price-chg" style="color:var(--dim)">—</div>
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

// ── View switcher (現金流 / 趨勢 / 比較) ──────────────────────
function setView(v){
  currentView = v;
  document.getElementById('tabCF').classList.toggle('active',      v==='cf');
  document.getElementById('tabTrend').classList.toggle('active',   v==='trend');
  document.getElementById('tabDiv').classList.toggle('active',     v==='div');
  document.getElementById('tabRev').classList.toggle('active',     v==='rev');
  document.getElementById('tabCompare').classList.toggle('active', v==='compare');
  document.getElementById('cf-section').style.display      = v==='cf'      ? 'block' : 'none';
  document.getElementById('trend-section').style.display   = v==='trend'   ? 'block' : 'none';
  document.getElementById('div-section').style.display     = v==='div'     ? 'block' : 'none';
  document.getElementById('rev-section').style.display     = v==='rev'     ? 'block' : 'none';
  document.getElementById('compare-section').style.display = v==='compare' ? 'block' : 'none';
  const toggle = document.getElementById('periodToggle');
  if(v==='cf') toggle.style.display = currentStockData?.has_quarterly ? 'flex' : 'none';
  else toggle.style.display = 'none';
  if(v==='trend') loadTrend(currentTicker, currentRange);
  if(v==='div') loadDividend(currentTicker);
  if(v==='rev') loadFinancials(currentTicker, revPeriod);
  if(v==='compare'){
    if(currentTicker && !cmpTickers.includes(currentTicker)) cmpTickers.push(currentTicker);
    renderCmpChips();
    loadCompare();
  }
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
  document.getElementById('div-section').style.display     = 'none';
  document.getElementById('rev-section').style.display     = 'none';
  document.getElementById('compare-section').style.display = 'none';
  document.getElementById('tabDiv').classList.remove('active');
  document.getElementById('tabRev').classList.remove('active');
  document.getElementById('tabCompare').classList.remove('active');
  currentRevData   = null;
  currentDivData   = null;
  currentTrendData = null;

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

// ── Dividend chart ────────────────────────────────────────────
async function loadDividend(ticker){
  if(!ticker) return;
  document.getElementById('divStats').innerHTML = '<div style="color:var(--muted);font-size:.82rem">載入中…</div>';
  document.getElementById('divTable').innerHTML = '';
  if(divChart){ divChart.destroy(); divChart=null; }
  const res = await fetch(`/api/stocks/${ticker}/dividends`);
  if(!res.ok){ document.getElementById('divStats').innerHTML='<div style="color:var(--muted)">無法取得股息資料</div>'; return; }
  const d = await res.json();
  currentDivData = d;
  renderDividend(d);
}

function renderDividend(d){
  const statsEl = document.getElementById('divStats');
  if(!d.has_dividends){
    statsEl.innerHTML = '<div style="color:var(--muted);font-size:.88rem;padding:20px 0">此股票目前不配息</div>';
    document.getElementById('divTable').innerHTML = '';
    return;
  }
  const st = d.stats || {};
  statsEl.innerHTML = `
    <div class="stat-card">
      <div class="v" style="color:#facc15">$${st.trailing_annual?.toFixed(2) ?? 'N/A'}</div>
      <div class="l">年度股息 / 股</div>
    </div>
    <div class="stat-card">
      <div class="v" style="color:var(--green)">${st.yield_pct!=null ? st.yield_pct.toFixed(2)+'%' : 'N/A'}</div>
      <div class="l">殖利率</div>
    </div>
    <div class="stat-card">
      <div class="v" style="color:#e2e8f0">$${st.last_amount?.toFixed(4) ?? 'N/A'}</div>
      <div class="l">最近一次股息</div>
    </div>
    <div class="stat-card">
      <div class="v" style="color:var(--muted);font-size:.95rem">${st.last_date ?? 'N/A'}</div>
      <div class="l">最近付息日</div>
    </div>`;

  // Annual bar chart
  const ann = d.annual;
  if(divChart) divChart.destroy();
  const ctx = document.getElementById('divChart').getContext('2d');
  divChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ann.labels,
      datasets: [{
        label: '年度股息 / 股 ($)',
        data: ann.dividends,
        backgroundColor: 'rgba(250,204,21,.72)',
        borderColor: 'rgba(250,204,21,1)',
        borderWidth: 1,
        borderRadius: 4,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position:'bottom', labels:{ color:'#cdd6f4', usePointStyle:true, padding:16 }},
        tooltip: { backgroundColor:'#0f3460', titleColor:'#e2e8f0', bodyColor:'#94a3b8',
          callbacks:{ label: c => ` $${c.parsed.y.toFixed(4)}` }},
        datalabels: {
          display: true, color:'#facc15', anchor:'end', align:'top',
          font:{size:9, weight:'bold'}, formatter: v => `$${v.toFixed(2)}`,
        },
      },
      scales: {
        x:{ ticks:{color:'#94a3b8', font:{size:10}}, grid:{color:'rgba(255,255,255,0.04)'} },
        y:{ ticks:{color:'#94a3b8', callback: v=>`$${v.toFixed(2)}`}, grid:{color:'rgba(255,255,255,0.06)'} },
      },
    },
  });

  // Payment history table (most recent first)
  const yoyMap = {};
  ann.labels.forEach((yr,i)=>{
    if(i>0) yoyMap[yr] = ann.dividends[i-1] > 0
      ? ((ann.dividends[i]-ann.dividends[i-1])/ann.dividends[i-1]*100).toFixed(1)
      : null;
  });

  const rows = [...d.dates].reverse().map((dt,i)=>{
    const amt = [...d.amounts].reverse()[i];
    const yr  = dt.slice(0,4);
    let yoy   = '–';
    if(yoyMap[yr]!=null){
      const p = parseFloat(yoyMap[yr]);
      const col = p>=0 ? 'var(--green)' : 'var(--red)';
      yoy = `<span style="color:${col}">${p>=0?'+':''}${p}%</span>`;
      delete yoyMap[yr]; // show YoY only once per year (first occurrence)
    }
    return `<tr><td>${dt}</td><td style="color:#facc15">$${amt.toFixed(4)}</td><td>${yoy}</td></tr>`;
  }).join('');
  document.getElementById('divTable').innerHTML = rows;
}

// ── Revenue / EPS chart ───────────────────────────────────────
async function loadFinancials(ticker, period){
  if(!ticker) return;
  if(currentRevData){
    renderFinancials(currentRevData, period);
    return;
  }
  document.getElementById('revStats').innerHTML = '<div style="color:var(--muted);font-size:.82rem">載入中…</div>';
  document.getElementById('revTable').innerHTML = '';
  if(revChart){ revChart.destroy(); revChart=null; }
  const res = await fetch(`/api/stocks/${ticker}/financials`);
  if(!res.ok){ document.getElementById('revStats').innerHTML='<div style="color:var(--muted)">無法取得財務資料</div>'; return; }
  const d = await res.json();
  currentRevData = d;
  // Show/hide quarterly toggle
  document.getElementById('revPeriodRow').style.display = d.has_financials && d.has_quarterly ? 'flex' : 'none';
  renderFinancials(d, period);
}

function setRevPeriod(p){
  revPeriod = p;
  document.getElementById('revBtnAnnual').classList.toggle('active',    p==='annual');
  document.getElementById('revBtnQuarterly').classList.toggle('active', p==='quarterly');
  renderFinancials(currentRevData, p);
}

function renderFinancials(d, period){
  const statsEl = document.getElementById('revStats');
  if(!d || !d.has_financials){
    statsEl.innerHTML = '<div style="color:var(--muted);font-size:.88rem;padding:20px 0">此股票無財務報表資料（如 ETF）</div>';
    document.getElementById('revTable').innerHTML = '';
    return;
  }
  const k = d.kpis || {};
  statsEl.innerHTML = `
    <div class="stat-card">
      <div class="v" style="color:#60a5fa">${k.latest_rev!=null ? (k.latest_rev>=1000?'$'+(k.latest_rev/1000).toFixed(2)+'B':'$'+k.latest_rev.toFixed(0)+'M') : 'N/A'}</div>
      <div class="l">最新年度營收</div>
    </div>
    <div class="stat-card">
      <div class="v" style="color:var(--orange)">${k.rev_cagr!=null ? k.rev_cagr.toFixed(1)+'%' : 'N/A'}</div>
      <div class="l">營收 CAGR</div>
    </div>
    <div class="stat-card">
      <div class="v" style="color:#4ade80">${k.latest_ni!=null ? (k.latest_ni>=1000?'$'+(k.latest_ni/1000).toFixed(2)+'B':'$'+k.latest_ni.toFixed(0)+'M') : 'N/A'}</div>
      <div class="l">最新年度淨利</div>
    </div>
    <div class="stat-card">
      <div class="v" style="color:#fb923c">${k.latest_eps!=null ? '$'+k.latest_eps.toFixed(2) : 'N/A'}</div>
      <div class="l">稀釋 EPS</div>
    </div>`;

  const series = (period==='quarterly' && d.quarterly) ? d.quarterly : d.annual;

  // Table
  const rows = series.labels.map((lbl, i) => {
    const rev = series.revenue[i], prev = i > 0 ? series.revenue[i-1] : null;
    let yoy = '–';
    if(rev!=null && prev!=null && prev!==0){
      const p = ((rev - prev) / Math.abs(prev) * 100).toFixed(1);
      const col = p >= 0 ? 'var(--green)' : 'var(--red)';
      yoy = `<span style="color:${col}">${p>=0?'+':''}${p}%</span>`;
    }
    const fmtRev = v => v==null ? 'N/A' : (Math.abs(v)>=1000 ? '$'+(v/1000).toFixed(2)+'B' : '$'+v.toFixed(0)+'M');
    const eps = series.eps[i];
    return `<tr>
      <td>${lbl}</td>
      <td style="color:#60a5fa">${fmtRev(series.revenue[i])}</td>
      <td>${yoy}</td>
      <td style="color:#4ade80">${fmtRev(series.net_income[i])}</td>
      <td style="color:#fb923c">${eps!=null ? '$'+eps.toFixed(2) : 'N/A'}</td>
    </tr>`;
  }).join('');
  document.getElementById('revTable').innerHTML = rows;

  // Chart (dual axis: revenue bars left, EPS line right)
  if(revChart) revChart.destroy();
  const ctx = document.getElementById('revChart').getContext('2d');
  revChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: series.labels,
      datasets: [
        {
          label: '總營收', data: series.revenue,
          backgroundColor: 'rgba(96,165,250,.65)', borderColor: 'rgba(96,165,250,1)',
          borderWidth: 1, borderRadius: 3, yAxisID: 'yRev',
          datalabels: { display: false },
        },
        {
          label: '淨利', data: series.net_income,
          backgroundColor: 'rgba(74,222,128,.55)', borderColor: 'rgba(74,222,128,1)',
          borderWidth: 1, borderRadius: 3, yAxisID: 'yRev',
          datalabels: { display: false },
        },
        {
          label: '稀釋 EPS', data: series.eps,
          type: 'line', borderColor: 'rgba(251,146,60,1)', backgroundColor: 'rgba(251,146,60,.12)',
          borderWidth: 2.5, pointRadius: 4, pointHoverRadius: 7, fill: false, tension: .3,
          yAxisID: 'yEps',
          datalabels: {
            display: c => series.labels.length <= 8 || c.dataIndex % 2 === 0,
            color: '#fb923c', anchor: 'end', align: 'top', font: {size:9, weight:'bold'},
            formatter: v => v!=null ? '$'+v.toFixed(2) : '',
          },
        },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'bottom', labels: { color: '#cdd6f4', usePointStyle: true, padding: 18 }},
        tooltip: {
          backgroundColor: '#0f3460', titleColor: '#e2e8f0', bodyColor: '#94a3b8',
          callbacks: {
            label: c => {
              const v = c.parsed.y;
              if(v == null) return `${c.dataset.label}: N/A`;
              if(c.dataset.yAxisID === 'yEps') return ` ${c.dataset.label}: $${v.toFixed(2)}`;
              return ` ${c.dataset.label}: ${Math.abs(v)>=1000 ? '$'+(v/1000).toFixed(2)+'B' : '$'+v.toFixed(0)+'M'}`;
            }
          }
        },
        datalabels: { display: false },
      },
      scales: {
        x: { ticks:{color:'#94a3b8', font:{size:10}}, grid:{color:'rgba(255,255,255,0.04)'} },
        yRev: {
          position: 'left',
          ticks: { color:'#94a3b8', callback: v => Math.abs(v)>=1000 ? `$${(v/1000).toFixed(0)}B` : `$${v}M` },
          grid: { color:'rgba(255,255,255,0.06)' },
        },
        yEps: {
          position: 'right',
          ticks: { color:'#fb923c', callback: v => `$${v.toFixed(1)}` },
          grid: { display: false },
        },
      },
    },
  });
}

// ── Export CSV / Excel ────────────────────────────────────────
function exportData(format){
  const ticker = currentTicker || 'export';
  let headers, rows, sheetName, filename;

  if(currentView === 'cf'){
    const s = currentStockData;
    if(!s || !s.annual){ toast('無可匯出的現金流資料'); return; }
    const series = (currentPeriod === 'quarterly' && s.has_quarterly) ? s.quarterly : s.annual;
    headers = ['期間', 'OCF ($M)', 'CapEx ($M)', '利息費用 ($M)', 'FCF ($M)', 'FCF轉換率'];
    rows = series.labels.map((lbl, i) => {
      const conv = (series.fcf[i] != null && series.ocf[i])
        ? (series.fcf[i] / series.ocf[i] * 100).toFixed(1) + '%' : '';
      return [lbl, series.ocf[i] ?? '', series.capex[i] ?? '', series.interest[i] ?? '', series.fcf[i] ?? '', conv];
    });
    sheetName = '現金流';
    filename = `${ticker}_cashflow_${currentPeriod}`;

  } else if(currentView === 'rev'){
    if(!currentRevData || !currentRevData.has_financials){ toast('無可匯出的財務資料'); return; }
    const series = (revPeriod === 'quarterly' && currentRevData.quarterly) ? currentRevData.quarterly : currentRevData.annual;
    headers = ['期間', '總營收 ($M)', '淨利 ($M)', '稀釋EPS ($)'];
    rows = series.labels.map((lbl, i) => [lbl, series.revenue[i] ?? '', series.net_income[i] ?? '', series.eps[i] ?? '']);
    sheetName = '營收EPS';
    filename = `${ticker}_revenue_${revPeriod}`;

  } else if(currentView === 'div'){
    if(!currentDivData || !currentDivData.has_dividends){ toast('此股票不配息，無資料可匯出'); return; }
    headers = ['付息日', '股息/股 ($)'];
    rows = currentDivData.dates.map((dt, i) => [dt, currentDivData.amounts[i] ?? '']);
    sheetName = '股息歷史';
    filename = `${ticker}_dividends`;

  } else if(currentView === 'trend'){
    if(!currentTrendData){ toast('請先載入趨勢圖'); return; }
    const d = currentTrendData;
    const [lbl1, lbl2] = d.ma_labels || ['MA20', 'MA50'];
    headers = ['日期', '收盤價 ($)', '成交量', lbl1, lbl2];
    rows = d.dates.map((dt, i) => [dt, d.close[i] ?? '', d.volume[i] ?? '', d.ma20[i] ?? '', d.ma50[i] ?? '']);
    sheetName = '價格趨勢';
    filename = `${ticker}_trend_${currentRange}`;

  } else {
    toast('此頁籤不支援匯出');
    return;
  }

  if(format === 'csv'){
    const escape = v => { const s = String(v); return (s.includes(',') || s.includes('"') || s.includes('\n')) ? `"${s.replace(/"/g,'""')}"` : s; };
    const csv = [headers, ...rows].map(r => r.map(escape).join(',')).join('\r\n');
    const blob = new Blob(['\ufeff' + csv], {type: 'text/csv;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename + '.csv'; a.click();
    URL.revokeObjectURL(url);

  } else if(format === 'xlsx'){
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.aoa_to_sheet([headers, ...rows]);
    XLSX.utils.book_append_sheet(wb, ws, sheetName);
    XLSX.writeFile(wb, filename + '.xlsx');
  }
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
  currentTrendData = d;
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

  // Thin date labels
  const is1D = d.period === '1d';
  const isMultiYear = d.period === '2y' || d.period === '5y';
  const skip = Math.max(1, Math.floor(d.dates.length / 8));
  const fmtTick = dt => is1D ? dt : isMultiYear ? dt.slice(2,7) : dt.slice(5);

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
            callback: (val, i) => i % skip === 0 ? fmtTick(d.dates[i]) : '' },
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
            callback: (val, i) => i % skip === 0 ? fmtTick(d.dates[i]) : '' },
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

// ── Compare ───────────────────────────────────────────────────
// Input autocomplete
let cmpSearchDebounce = null;
(function(){
  const inp = document.getElementById('cmpInput');
  const ddEl = document.getElementById('cmpDropdown');

  inp.addEventListener('input', ()=>{
    clearTimeout(cmpSearchDebounce);
    cmpSearchDebounce = setTimeout(doCmpSearch, 200);
  });
  inp.addEventListener('keydown', e=>{
    if(e.key === 'Enter'){ ddEl.style.display='none'; addCmpTicker(); }
    if(e.key === 'Escape'){ ddEl.style.display='none'; }
  });
  document.addEventListener('click', e=>{
    if(!e.target.closest('.cmp-input-wrap')) ddEl.style.display='none';
  });

  async function doCmpSearch(){
    const q = inp.value.trim();
    if(q.length < 1){ ddEl.style.display='none'; return; }
    const res = await fetch(`/api/catalog?q=${encodeURIComponent(q)}`);
    const items = await res.json();
    if(!items.length){ ddEl.style.display='none'; return; }
    ddEl.innerHTML = items.slice(0,10).map(s=>`
      <div class="dd-item" onclick="pickCmpSearch('${s.ticker}')">
        <div>
          <span style="font-weight:700;color:#e2e8f0">${s.ticker}</span>
          <span class="dd-in"> &nbsp;${s.name}</span>
        </div>
        <span class="dd-ex ${s.exchange}">${s.exchange}</span>
      </div>`).join('');
    ddEl.style.display = 'block';
  }
})();

function pickCmpSearch(ticker){
  document.getElementById('cmpDropdown').style.display = 'none';
  document.getElementById('cmpInput').value = '';
  if(cmpTickers.length >= 8){ toast('最多比較 8 檔股票'); return; }
  if(!cmpTickers.includes(ticker)) cmpTickers.push(ticker);
  renderCmpChips();
  loadCompare();
}

function setCmpRange(btn){
  document.querySelectorAll('#cmpRangeRow .range-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  cmpRange = btn.dataset.p;
  loadCompare();
}

function addCmpTicker(){
  document.getElementById('cmpDropdown').style.display = 'none';
  const v = document.getElementById('cmpInput').value.trim().toUpperCase();
  document.getElementById('cmpInput').value = '';
  if(!v) return;
  if(cmpTickers.length >= 8){ toast('最多比較 8 檔股票'); return; }
  if(!cmpTickers.includes(v)) cmpTickers.push(v);
  renderCmpChips();
  loadCompare();
}

function removeCmpTicker(t){
  cmpTickers = cmpTickers.filter(x => x !== t);
  renderCmpChips();
  loadCompare();
}

function renderCmpChips(){
  document.getElementById('cmpChips').innerHTML = cmpTickers.map((t,i)=>{
    const col = CMP_COLORS[i % CMP_COLORS.length];
    return `<span class="cmp-chip" style="border-color:${col};color:${col}">${t
      }<button class="rm" onclick="removeCmpTicker('${t}')">✕</button></span>`;
  }).join('');
}

async function loadCompare(){
  if(cmpTickers.length === 0){
    if(cmpChart){ cmpChart.destroy(); cmpChart = null; }
    document.getElementById('cmpChart').getContext('2d').clearRect(0,0,9999,9999);
    return;
  }
  const res = await fetch(`/api/compare?tickers=${cmpTickers.join(',')}&period=${cmpRange}`);
  if(!res.ok){ toast('比較資料載入失敗'); return; }
  renderCompare(await res.json());
}

function renderCompare(d){
  const dates  = d.dates || [];
  const is1D   = d.period === '1d';
  const skip   = Math.max(1, Math.floor(dates.length / 8));
  const entries = Object.entries(d.tickers);

  const datasets = entries.map(([ticker, data], i)=>{
    const col = CMP_COLORS[i % CMP_COLORS.length];
    return {
      label: ticker,
      data: data.normalized,
      borderColor: col,
      backgroundColor: col.replace('1)','0.12)'),
      borderWidth: 2,
      pointRadius: 0,
      pointHoverRadius: 5,
      fill: false,
      tension: 0.2,
    };
  });

  if(cmpChart) cmpChart.destroy();
  const ctx = document.getElementById('cmpChart').getContext('2d');
  cmpChart = new Chart(ctx, {
    type: 'line',
    data: { labels: dates, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position:'bottom', labels:{ color:'#cdd6f4', usePointStyle:true, padding:16, font:{size:11} }},
        tooltip: {
          backgroundColor:'#0f3460', titleColor:'#e2e8f0', bodyColor:'#94a3b8',
          callbacks: {
            title: items => items[0].label,
            label: c => {
              const ticker = c.dataset.label;
              const norm   = c.parsed.y;
              const actual = d.tickers[ticker]?.close[c.dataIndex];
              const sign   = norm >= 0 ? '+' : '';
              return ` ${ticker}: ${sign}${norm?.toFixed(2)}%  ($${actual?.toFixed(2)})`;
            }
          }
        },
        datalabels: { display: false },
      },
      scales: {
        x: {
          ticks: { color:'#94a3b8', font:{size:10}, maxRotation:0,
            callback: (val,i) => i % skip === 0 ? (is1D ? dates[i] : (dates[i]?.slice(5)||'')) : '' },
          grid: { color:'rgba(255,255,255,0.04)' },
        },
        y: {
          ticks: { color:'#94a3b8', font:{size:10},
            callback: v => (v >= 0 ? '+' : '') + v.toFixed(1) + '%' },
          grid: { color:'rgba(255,255,255,0.06)' },
        },
      },
    },
  });
}

// ── Screener ───────────────────────────────────────────────────
let screenerVisible = false;

async function toggleScreener(){
  screenerVisible = !screenerVisible;
  const panel = document.getElementById('screener-panel');
  panel.style.display = screenerVisible ? 'block' : 'none';
  if(screenerVisible){
    const res = await fetch('/api/sectors');
    const sects = await res.json();
    const sel = document.getElementById('scrSector');
    sel.innerHTML = '<option value="">全部產業</option>' +
      sects.map(s=>`<option value="${s}">${s}</option>`).join('');
    runScreener();
  }
}

async function runScreener(){
  const params = new URLSearchParams();
  const sect     = document.getElementById('scrSector').value;
  const minCagr  = document.getElementById('scrMinCagr').value;
  const minFcf   = document.getElementById('scrMinFcfConv').value;
  const minPe    = document.getElementById('scrMinPe').value;
  const maxPe    = document.getElementById('scrMaxPe').value;
  if(currentExchange !== 'ALL') params.set('exchange', currentExchange);
  if(sect)    params.set('sector',       sect);
  if(minCagr) params.set('min_cagr',    minCagr);
  if(minFcf)  params.set('min_fcf_conv', minFcf);
  if(minPe)   params.set('min_pe',      minPe);
  if(maxPe)   params.set('max_pe',      maxPe);
  const res = await fetch('/api/screener?' + params.toString());
  renderScreener(await res.json());
}

function resetScreener(){
  ['scrMinCagr','scrMinFcfConv','scrMinPe','scrMaxPe'].forEach(id=>document.getElementById(id).value='');
  document.getElementById('scrSector').value = '';
  runScreener();
}

function renderScreener(stocks){
  const inDbCount = stocks.filter(s => s.in_db !== false).length;
  const note = inDbCount < stocks.length
    ? `（${inDbCount} 檔已載入數據，其餘點「載入」抓取）`
    : '';
  document.getElementById('scrCount').textContent = `共 ${stocks.length} 檔 ${note}`;
  const tbody = document.getElementById('scrBody');
  if(!stocks.length){
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;color:var(--dim);padding:30px">無符合條件的股票</td></tr>`;
    return;
  }
  tbody.innerHTML = stocks.map(s=>{
    const hasData = s.in_db !== false;
    const k = s.kpis || {};
    const ex = s.exchange || '';
    const rowStyle = hasData ? 'cursor:pointer' : 'cursor:pointer;opacity:.6';
    const cagrColor = k.ocf_cagr     >= 10 ? 'var(--green)' : 'var(--text)';
    const convColor = k.fcf_conversion >= 70 ? 'var(--green)' : 'var(--text)';
    const dash = `<span style="color:var(--dim)">—</span>`;
    const btnLabel = hasData ? '查看' : '載入';
    return `<tr style="${rowStyle}" onclick="scrPick('${s.ticker}')">
      <td><strong style="color:${hasData?'#e2e8f0':'var(--muted)'}">${s.ticker}</strong></td>
      <td style="color:var(--muted);max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${s.name||''}</td>
      <td><span class="ex-badge ${ex}" style="font-size:.65rem">${ex}</span></td>
      <td style="color:var(--dim);font-size:.76rem">${s.sector||dash}</td>
      <td>${hasData&&s.current_price!=null?'$'+s.current_price.toFixed(2):dash}</td>
      <td style="color:${cagrColor}">${hasData?(k.ocf_cagr!=null?k.ocf_cagr.toFixed(1)+'%':'N/A'):dash}</td>
      <td style="color:${convColor}">${hasData?(k.fcf_conversion!=null?k.fcf_conversion.toFixed(0)+'%':'N/A'):dash}</td>
      <td style="color:var(--purple)">${hasData?(k.pe_ratio!=null?k.pe_ratio.toFixed(1):'N/A'):dash}</td>
      <td><button class="btn btn-refresh" style="font-size:.7rem;padding:3px 9px" onclick="event.stopPropagation();scrPick('${s.ticker}')">${btnLabel}</button></td>
    </tr>`;
  }).join('');
}

async function scrPick(ticker){
  const inDb = await isInDb(ticker);
  if(!inDb){
    toast('載入中...');
    const res = await fetch('/api/stocks',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ticker})});
    const d = await res.json();
    if(!res.ok){toast('Error: '+d.error);return;}
    toast(`已加入 ${d.name}`);
  } else {
    await fetch(`/api/stocks/${ticker}/pin`, {method:'POST'});
  }
  await loadMyStocks();
  runScreener();
  showChart(ticker);
}

// ── Bulk fetch ────────────────────────────────────────────────
function startBulkFetch(){
  const btn  = document.getElementById('btnBulk');
  const wrap = document.getElementById('bulkBarWrap');
  const fill = document.getElementById('bulkFill');
  const stat = document.getElementById('bulkStatus');
  btn.disabled = true;
  btn.textContent = '載入中...';
  wrap.style.display = 'block';
  fill.style.width = '0%';
  stat.textContent = '正在連線...';

  const es = new EventSource('/api/bulk-fetch');
  es.onmessage = e => {
    const d = JSON.parse(e.data);
    const pct = d.total > 0 ? Math.round(d.done / d.total * 100) : 0;
    fill.style.width = pct + '%';
    if(d.finished){
      stat.textContent = `完成！已載入 ${d.total} 檔數據`;
      btn.disabled = false;
      btn.textContent = '&#8987; 載入全部數據';
      es.close();
      loadMyStocks();
      runScreener();
    } else {
      stat.textContent = `${d.done} / ${d.total}  正在載入 ${d.ticker}...`;
    }
  };
  es.onerror = () => {
    stat.textContent = '連線中斷，請重試';
    btn.disabled = false;
    btn.textContent = '&#8987; 載入全部數據';
    es.close();
  };
}

// ── Backup history ────────────────────────────────────────────
function startBackupHistory(){
  const btn  = document.getElementById('btnBackup');
  const wrap = document.getElementById('bulkBarWrap');
  const fill = document.getElementById('bulkFill');
  const stat = document.getElementById('bulkStatus');
  btn.disabled = true;
  btn.textContent = '備份中...';
  wrap.style.display = 'block';
  fill.style.width = '0%';
  stat.textContent = '正在連線...';

  const es = new EventSource('/api/backup-history');
  es.onmessage = e => {
    const d = JSON.parse(e.data);
    const pct = d.total > 0 ? Math.round(d.done / d.total * 100) : 0;
    fill.style.width = pct + '%';
    if(d.finished){
      stat.textContent = `備份完成！共 ${d.total} 檔（股息 / 財務 / 1y + 5y 價格歷史）`;
      btn.disabled = false;
      btn.textContent = '&#128190; 備份歷史資料';
      es.close();
    } else {
      const err = d.error ? ` ⚠` : '';
      stat.textContent = `${d.done} / ${d.total}  備份中 ${d.ticker}${err}`;
    }
  };
  es.onerror = () => {
    stat.textContent = '連線中斷，請重試';
    btn.disabled = false;
    btn.textContent = '&#128190; 備份歷史資料';
    es.close();
  };
}

// ── Live price stream (SSE) ───────────────────────────────────
let priceSSE = null;

function startPriceStream(){
  if(priceSSE){ priceSSE.close(); priceSSE = null; }
  const dot = document.getElementById('liveDot');
  if(dot){ dot.title = '即時報價：連線中'; dot.classList.remove('active'); }
  priceSSE = new EventSource('/api/prices/stream');
  priceSSE.onopen = () => {
    if(dot){ dot.classList.add('active'); dot.title = '即時報價：已連線（每30秒更新）'; }
  };
  priceSSE.onmessage = e => {
    try {
      const updates = JSON.parse(e.data);
      if(!Array.isArray(updates) || !updates.length) return;
      updates.forEach(applyPriceUpdate);
      if(dot){ dot.title = '即時報價：最後更新 ' + new Date().toLocaleTimeString('zh-TW'); }
    } catch(err){}
  };
  priceSSE.onerror = () => {
    if(dot){ dot.classList.remove('active'); dot.title = '即時報價：連線中斷，10秒後重試'; }
    priceSSE.close(); priceSSE = null;
    setTimeout(startPriceStream, 10000);
  };
}

function applyPriceUpdate(u){
  const card = document.getElementById('card-' + u.ticker);
  if(!card) return;
  const priceEl = card.querySelector('.price');
  if(priceEl && u.price != null){
    const prev = parseFloat(priceEl.textContent.replace('$',''));
    const newTxt = '$' + u.price.toFixed(2);
    if(priceEl.textContent !== newTxt){
      priceEl.textContent = newTxt;
      priceEl.classList.remove('price-up','price-dn');
      void priceEl.offsetWidth;
      if(!isNaN(prev)) priceEl.classList.add(u.price >= prev ? 'price-up' : 'price-dn');
    }
  }
  const chgEl = card.querySelector('.price-chg');
  if(chgEl && u.change_pct != null){
    const sign = u.change_pct >= 0 ? '+' : '';
    chgEl.textContent = sign + u.change_pct.toFixed(2) + '%';
    chgEl.style.color = u.change_pct >= 0 ? 'var(--green)' : 'var(--red)';
  }
}

// ── Init ──────────────────────────────────────────────────────
(async function(){
  await loadPopular();
  await loadMyStocks();
  startPriceStream();
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
