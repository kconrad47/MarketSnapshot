import pandas as pd
import yfinance as yf
import requests
from datetime import datetime, timedelta
import os
import json
import plotly.graph_objects as go
import plotly.io as pio
from dotenv import load_dotenv # Added for python-dotenv

# Load environment variables from .env file
load_dotenv() # Added for python-dotenv

# --- Configuration ---
# Removed the hardcoded default value for security. 
# FRED_API_KEY must now be set as an environment variable (e.g., in a .env file or system-wide).
FRED_API_KEY = os.getenv("FRED_API_KEY") 
if not FRED_API_KEY:
    print("ERROR: FRED_API_KEY environment variable not set. Some fixed income and commodity index data may be unavailable.")
    # You might consider exiting here if FRED data is critical:
    # import sys
    # sys.exit("Exiting: FRED_API_KEY is required.")

TODAY_DT = datetime.now()
TODAY = pd.Timestamp(TODAY_DT)
THREE_MONTHS_AGO_FOR_FETCH = TODAY_DT - timedelta(days=95)


# --- Ticker and Series ID Definitions ---
US_EQUITY_TICKERS = {
    "S&P 500": "SPY", "QQQ (Nasdaq 100)": "QQQ", "Russell 2000": "IWM", "Real Estate (XLRE)": "XLRE",
    "Communication Services (XLC)": "XLC", "Technology (XLK)": "XLK", "Industrials (XLI)": "XLI",
    "Health Care (XLV)": "XLV", "Financials (XLF)": "XLF", "Consumer Staples (XLP)": "XLP",
    "Consumer Discretionary (XLY)": "XLY", "Energy (XLE)": "XLE", "Materials (XLB)": "XLB", "Utilities (XLU)": "XLU",
}
US_SENTIMENT_TICKERS = { "VIX Index": "^VIX", "VXN Index": "^VXN",}
GLOBAL_EQUITY_TICKERS = {
    "All Country World Index (ACWI)": "ACWI", "Developed Markets ex-NA (EFA)": "EFA", "Emerging Markets (EEM)": "EEM",
    "Argentina (ARGT)": "ARGT", "Brazil (EWZ)": "EWZ", "Canada (EWC)": "EWC", "Mexico (EWW)": "EWW",
    "Chile (ECH)": "ECH", "Colombia (GXG)": "GXG", "Peru (EPU)": "EPU", "France (EWQ)": "EWQ",
    "Germany (EWG)": "EWG", "Greece (GREK)": "GREK", "Italy (EWI)": "EWI", "Spain (EWP)": "EWP",
    "Switzerland (EWL)": "EWL", "United Kingdom (EWU)": "EWU", "Belgium (EWK)": "EWK", "Denmark (EDEN)": "EDEN",
    "Ireland (EIRL)": "EIRL", "Finland (EFNL)": "EFNL", "Sweden (EWD)": "EWD", "Austria (EWO)": "EWO",
    "Norway (ENOR)": "ENOR", "Poland (EPOL)": "EPOL", "Australia (EWA)": "EWA", "China (Large-Cap) (GXC)": "GXC",
    "Hong Kong (EWH)": "EWH", "India (PIN)": "PIN", "Japan (EWJ)": "EWJ", "South Korea (EWY)": "EWY",
    "Taiwan (EWT)": "EWT", "Singapore (EWS)": "EWS", "Vietnam (VNM)": "VNM", "New Zealand (ENZL)": "ENZL",
    "Indonesia (EIDO)": "EIDO", "Israel (EIS)": "EIS", "Saudi Arabia (KSA)": "KSA", "South Africa (EZA)": "EZA",
    "UAE (UAE)": "UAE", "Turkey (TUR)": "TUR", "Qatar (QAT)": "QAT",
}
FRED_FIXED_INCOME_SERIES = {
    "3-Month T-Bill Yield": "DTB3", "2-Year T-Note Yield": "DGS2",
    "10-Year T-Bond Yield": "DGS10", "30-Year T-Bond Yield": "DGS30",
}
YFINANCE_FIXED_INCOME_TICKERS = {"MOVE Index": "^MOVE", "High Grade Bonds": "LQD", "High Yield Bonds": "HYG",}
COMMODITY_TICKERS = {
    "S&P GSCI": "^SPGSCI", "WTI Crude Oil": "CL=F", "Brent Crude Oil": "BZ=F", "Natural Gas": "NG=F",
    "Heating Oil": "HO=F", "Gasoline": "RB=F", "Silver": "SI=F", "Gold": "GC=F", "Copper": "HG=F",
    "Wheat": "ZW=F", "Live Cattle": "LE=F", "Feeder Cattle": "GF=F", "Soybeans": "ZS=F", "Corn": "ZC=F", "Sugar": "SB=F",
}
COMMODITY_INDEX_FRED_SERIES = {}
CRYPTO_TICKERS = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD",}
CURRENCY_TICKERS = {
    "DXY (US Dollar Index)": "DX-Y.NYB", "Japanese Yen": "JPY=X", "Euro": "EURUSD=X", "British Pound": "GBPUSD=X",
    "Swiss Franc": "CHF=X", "Australian Dollar": "AUDUSD=X", "Brazilian Real": "BRL=X", "Chinese Yuan": "CNY=X",
    "Colombian Peso": "COP=X", "Hong Kong Dollar": "HKD=X", "Indonesian Rupiah": "IDR=X", "South Korean Won": "KRW=X",
    "Mexican Peso": "MXN=X", "Indian Rupee": "INR=X", "Philippine Peso": "PHP=X", "Malaysian Ringgit": "MYR=X",
    "Singapore Dollar": "SGD=X", "Thai Baht": "THB=X", "Turkish Lira": "TRY=X", "New Taiwan Dollar": "TWD=X",
    "South African Rand": "ZAR=X",
}

# --- Helper Functions ---
def get_yfinance_data(ticker_symbol, start_date, end_date):
    try:
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')

        data = yf.download(ticker_symbol, start=start_str, end=end_str, progress=False, auto_adjust=True)
        if data.empty:
            print(f"Warning: No data found for {ticker_symbol} between {start_str} and {end_str}")
            return pd.DataFrame()
        data.index = pd.to_datetime(data.index).normalize()
        return data[['Close']].copy() # This returns a DataFrame
    except Exception as e:
        print(f"Error fetching Yahoo Finance data for {ticker_symbol}: {e}")
        return pd.DataFrame()

def calculate_yfinance_performance(ticker_symbol, current_price_df):
    performance = {"Day": "N/A", "Week": "N/A", "Month": "N/A"}
    if current_price_df.empty or 'Close' not in current_price_df.columns: return performance
    current_price_df = current_price_df.sort_index()
    if current_price_df.empty: return performance
    # current_price_df is a DataFrame with one column 'Close'
    # .iloc[-1] selects the last row (still a Series)
    # .item() extracts the scalar value if the Series has only one element
    current_price = current_price_df['Close'].iloc[-1].item() if not current_price_df.empty else None
    if current_price is None: return performance

    if len(current_price_df) >= 2:
        prev_day_close = current_price_df['Close'].iloc[-2].item()
        if prev_day_close != 0: performance["Day"] = ((current_price - prev_day_close) / prev_day_close) * 100

    one_week_ago_date = (TODAY - pd.Timedelta(days=7)).normalize()
    week_ago_df_slice = current_price_df[current_price_df.index <= one_week_ago_date]
    if not week_ago_df_slice.empty:
        price_week_ago = week_ago_df_slice['Close'].iloc[-1].item()
        if price_week_ago != 0: performance["Week"] = ((current_price - price_week_ago) / price_week_ago) * 100

    one_month_ago_date = (TODAY - pd.Timedelta(days=30)).normalize()
    month_ago_df_slice = current_price_df[current_price_df.index <= one_month_ago_date]
    if not month_ago_df_slice.empty:
        price_month_ago = month_ago_df_slice['Close'].iloc[-1].item()
        if price_month_ago != 0: performance["Month"] = ((current_price - price_month_ago) / price_month_ago) * 100
    return performance

def get_fred_data(series_id, api_key, start_date, end_date):
    if not api_key: # Added check for missing API key
        print(f"Skipping FRED data fetch for {series_id}: API key is not set.")
        return pd.Series(dtype=float)
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json&observation_start={start_date.strftime('%Y-%m-%d')}&observation_end={end_date.strftime('%Y-%m-%d')}"
    try:
        response = requests.get(url); response.raise_for_status(); data = json.loads(response.text)
        if 'observations' not in data or not data['observations']:
            print(f"Warning: No observations found for FRED series {series_id}.")
            return pd.Series(dtype=float)
        df = pd.DataFrame(data['observations'])
        df['date'] = pd.to_datetime(df['date']).dt.normalize()
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df = df.set_index('date')['value'].dropna()
        return df
    except Exception as e:
        print(f"Error fetching FRED data for {series_id}: {e}")
        return pd.Series(dtype=float)

def calculate_fred_performance(series_data):
    performance = {"Day": "N/A", "Week": "N/A", "Month": "N/A"}
    if series_data.empty: return performance
    series_data = series_data.sort_index()
    current_value = series_data.iloc[-1].item()
    if len(series_data) >= 2:
        prev_day_value = series_data.iloc[-2].item()
        performance["Day"] = (current_value - prev_day_value)

    one_week_ago_date = (TODAY - pd.Timedelta(days=7)).normalize()
    week_ago_series_slice = series_data[series_data.index <= one_week_ago_date]
    if not week_ago_series_slice.empty:
        value_week_ago = week_ago_series_slice.iloc[-1].item()
        performance["Week"] = (current_value - value_week_ago)

    one_month_ago_date = (TODAY - pd.Timedelta(days=30)).normalize()
    month_ago_series_slice = series_data[series_data.index <= one_month_ago_date]
    if not month_ago_series_slice.empty:
        value_month_ago = month_ago_series_slice.iloc[-1].item()
        performance["Month"] = (current_value - value_month_ago)
    return performance

def get_currency_performance(ticker_symbol, current_price_df):
    performance = {"Day": "N/A", "Week": "N/A", "Month": "N/A"}; current_rate = None
    if current_price_df.empty or 'Close' not in current_price_df.columns: return performance, current_rate
    current_price_df = current_price_df.sort_index()
    if current_price_df.empty: return performance, current_rate
    current_rate = current_price_df['Close'].iloc[-1].item()
    if current_rate is None: return performance, current_rate

    if len(current_price_df) >= 2:
        prev_day_rate = current_price_df['Close'].iloc[-2].item()
        if prev_day_rate != 0: performance["Day"] = ((current_rate - prev_day_rate) / prev_day_rate) * 100

    one_week_ago_date = (TODAY - pd.Timedelta(days=7)).normalize()
    week_ago_df_slice = current_price_df[current_price_df.index <= one_week_ago_date]
    if not week_ago_df_slice.empty:
        rate_week_ago = week_ago_df_slice['Close'].iloc[-1].item()
        if rate_week_ago != 0: performance["Week"] = ((current_rate - rate_week_ago) / rate_week_ago) * 100

    one_month_ago_date = (TODAY - pd.Timedelta(days=30)).normalize()
    month_ago_df_slice = current_price_df[current_price_df.index <= one_month_ago_date]
    if not month_ago_df_slice.empty:
        rate_month_ago = month_ago_df_slice['Close'].iloc[-1].item()
        if rate_month_ago != 0: performance["Month"] = ((current_rate - rate_month_ago) / rate_month_ago) * 100
    return performance, current_rate

def get_top_bottom_performers(df, column_name, num_performers=5):
    df_copy = df.copy(); df_copy[column_name] = pd.to_numeric(df_copy[column_name], errors='coerce')
    df_sorted = df_copy.dropna(subset=[column_name]).sort_values(by=column_name, ascending=False)
    return df_sorted.head(num_performers), df_sorted.tail(num_performers).sort_values(by=column_name, ascending=True)

def get_heatmap_class(value, min_col_val=None, max_col_val=None):
    if not isinstance(value, (int, float)): return "bg-gray-200 text-gray-800"
    if value == 0.0: return "bg-gray-300 text-gray-800"
    green_classes = ["bg-green-100", "bg-green-200", "bg-green-300", "bg-green-400", "bg-green-500"]
    red_classes = ["bg-red-100", "bg-red-200", "bg-red-300", "bg-red-400", "bg-red-500"]
    text_class = "text-gray-800"
    if value > 0:
        scale = 1.0 if (max_col_val is None or max_col_val <= 0) else min(value / max_col_val, 1.0)
        idx = max(0, min(int(scale ** 0.5 * (len(green_classes) -1)), len(green_classes) - 1))
        selected_class = green_classes[idx];
        if idx >= 3: text_class = "text-white"
    else:
        scale = 1.0 if (min_col_val is None or min_col_val >= 0) else min(abs(value) / abs(min_col_val), 1.0)
        idx = max(0, min(int(scale ** 0.5 * (len(red_classes) - 1)), len(red_classes) - 1))
        selected_class = red_classes[idx];
        if idx >= 3: text_class = "text-white"
    return f"{selected_class} {text_class}"

def create_html_table(df, table_id_for_title_check, apply_heatmap=True, value_format=".2f"):
    html_content = ""
    if table_id_for_title_check.startswith("A.") or table_id_for_title_check.startswith("B.") or table_id_for_title_check.startswith("C.") or table_id_for_title_check.startswith("D.") :
         html_content += f'<h3 class="text-xl font-semibold mb-2">{table_id_for_title_check}</h3>\n'
    html_content += '<div class="overflow-x-auto mb-8">\n<table class="min-w-full bg-white shadow-md rounded-lg overflow-hidden">\n'
    column_heatmap_ranges = {}
    if apply_heatmap:
        for col in df.columns:
            if "Change" in col or "Yield" in col or "Return" in col:
                numeric_values = pd.to_numeric(df[col], errors='coerce').dropna()
                if not numeric_values.empty: column_heatmap_ranges[col] = {'min': numeric_values.min(), 'max': numeric_values.max()}
    html_content += '  <thead class="bg-gray-100 border-b border-gray-200">\n<tr>\n'
    for col in df.columns: html_content += f'      <th class="py-2 px-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider sticky top-0 bg-gray-100">{col}</th>\n'
    html_content += '</tr>\n</thead>\n<tbody class="divide-y divide-gray-200">\n'
    for _, row in df.iterrows():
        html_content += '    <tr class="hover:bg-gray-50 transition-transform duration-200 transform hover:scale-[1.005]">\n'
        for col_name in df.columns:
            cell_value = row[col_name]; display_value = cell_value
            apply_cell_heatmap = apply_heatmap and col_name in column_heatmap_ranges
            if apply_cell_heatmap:
                min_val, max_val = column_heatmap_ranges[col_name]['min'], column_heatmap_ranges[col_name]['max']
                heatmap_class = get_heatmap_class(cell_value, min_val, max_val)
                if isinstance(cell_value, float):
                    suffix = "%" if "%" in col_name and not ("bps" in col_name or ("Yield" in col_name and "Change" in col_name)) else ""
                    display_value = f"{cell_value:{value_format}}{suffix}"
                html_content += f'      <td class="py-2 px-3 whitespace-nowrap text-sm leading-relaxed"><span class="block w-full text-center py-1 px-2 rounded-md {heatmap_class}">{display_value}</span></td>\n'
            else:
                if isinstance(cell_value, float):
                    if "Rate" in col_name and "FX Rates" in table_id_for_title_check: display_value = f"{cell_value:.4f}"
                    elif "Price" in col_name and "Crypto" in table_id_for_title_check: display_value = f"{cell_value:,.2f}"
                    else: display_value = f"{cell_value:.2f}"
                html_content += f'      <td class="py-2 px-3 whitespace-nowrap text-sm text-gray-700 leading-relaxed">{display_value}</td>\n'
        html_content += '    </tr>\n'
    html_content += '  </tbody>\n</table>\n</div>\n'
    return html_content

def generate_plotly_chart(data_df, title, y_col='Close', days_history=30):
    print(f"\n--- Debugging Chart: {title} ---")
    if data_df is None or data_df.empty: print("Initial data_df received is None or empty.")
    else:
        print(f"Initial data_df received (first 5, last 5 rows):"); print(data_df.head()); print(data_df.tail())
        print(f"data_df index type: {type(data_df.index)}, first: {data_df.index[0] if len(data_df.index) > 0 else 'N/A'}")
        print(f"data_df shape: {data_df.shape}")

    if data_df is None or data_df.empty or y_col not in data_df.columns:
        print(f"Chart data unavailable or y_col '{y_col}' missing."); return f"<div class='my-4 p-4 bg-red-100 text-red-700 rounded-md'>Chart data unavailable for {title}.</div>"

    if not isinstance(data_df.index, pd.DatetimeIndex):
        print("Index is not DatetimeIndex. Attempting conversion...");
        try: data_df.index = pd.to_datetime(data_df.index); print("Index converted to DatetimeIndex.")
        except Exception as e: print(f"Error converting index to DatetimeIndex: {e}"); return f"<div class='my-4 p-4 bg-red-100 text-red-700 rounded-md'>Chart data index is not datetime for {title}.</div>"

    data_df.index = data_df.index.normalize()
    print(f"data_df index after potential conversion & normalization (first 5): {data_df.index[:5]}")
    chart_df = data_df.sort_index().iloc[-days_history:]
    print(f"\nchart_df after slicing for {days_history} days (first 5, last 5 rows):")
    if not chart_df.empty: print(chart_df.head()); print(chart_df.tail())
    print(f"chart_df shape: {chart_df.shape}")

    if chart_df.empty or len(chart_df) < 2:
        print(f"Not enough data for {days_history}-day chart (found {len(chart_df)} points).")
        return f"<div class='my-4 p-4 bg-yellow-100 text-yellow-700 rounded-md'>Not enough data for {days_history}-day chart for {title} (found {len(chart_df)} points).</div>"

    fig = go.Figure()

    # --- ADDED DEBUGGING AND EXPLICIT SERIES SELECTION ---
    y_data_for_chart_candidate = chart_df[y_col]
    print(f"Type of y_data_for_chart_candidate (chart_df[y_col]): {type(y_data_for_chart_candidate)}")

    if isinstance(y_data_for_chart_candidate, pd.DataFrame):
        print(f"y_data_for_chart_candidate IS A DATAFRAME. Columns: {y_data_for_chart_candidate.columns}")
        if y_col in y_data_for_chart_candidate.columns and len(y_data_for_chart_candidate.columns) == 1:
            # This should be the case if data_df was [['Close']]
            y_data_series = y_data_for_chart_candidate[y_col] # Extract the Series
            print(f"Extracted Series from DataFrame. Type now: {type(y_data_series)}")
        elif not y_data_for_chart_candidate.empty: # If it's a multi-column DF or y_col is not the only one
             y_data_series = y_data_for_chart_candidate.iloc[:, 0] # Fallback: take the first column as Series
             print(f"y_data_for_chart_candidate was DataFrame, took first column. Type now: {type(y_data_series)}")
        else:
            print(f"y_data_for_chart_candidate is an empty DataFrame or y_col '{y_col}' not found directly.")
            return f"<div class='my-4 p-4 bg-red-100 text-red-700 rounded-md'>Could not extract y-data Series for {title}.</div>"
    elif isinstance(y_data_for_chart_candidate, pd.Series):
        print("y_data_for_chart_candidate IS ALREADY A SERIES.")
        y_data_series = y_data_for_chart_candidate
    else:
        print(f"y_data_for_chart_candidate is an unexpected type: {type(y_data_for_chart_candidate)}")
        return f"<div class='my-4 p-4 bg-red-100 text-red-700 rounded-md'>Unexpected y-data type for {title}.</div>"
    # --- END OF DEBUGGING AND EXPLICIT SERIES SELECTION ---

    fig.add_trace(go.Scatter(x=chart_df.index, y=y_data_series.tolist(), mode='lines+markers', name=y_col,
                             line=dict(color='royalblue', width=2), marker=dict(size=4)))

    fig.update_layout(title=dict(text=title, x=0.5, font=dict(size=16)), xaxis_title=None, yaxis_title="Price", margin=dict(l=50, r=20, t=50, b=20), height=350, template="plotly_white",
        xaxis=dict(type='date', showgrid=True, gridwidth=1, gridcolor='LightGrey'), yaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGrey'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

def generate_morning_report():
    print(f"Fetching data from: {THREE_MONTHS_AGO_FOR_FETCH.strftime('%Y-%m-%d')} to {TODAY.strftime('%Y-%m-%d')}")
    html_head = f"""
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Financial Market Report v3a</title><script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous"></script> <style>
body {{ font-family: 'Inter', sans-serif; background-color: #f3f4f6; color: #1f2937; padding: 20px; }}
.container {{ max-width: 1200px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); }}
h1, h2, h3 {{ color: #111827; }} h1 {{ font-size: 2.5rem; font-weight: 800; }}
h2 {{ font-size: 1.75rem; font-weight: 700; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; margin-top: 30px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }}
h2 .chevron-icon {{ transition: transform 0.3s ease; }} h2 .chevron-icon.rotate-90 {{ transform: rotate(-90deg); }}
h3 {{ font-size: 1.25rem; font-weight: 600; margin-top: 25px; margin-bottom: 10px; }}
h4 {{ font-size: 1.1rem; font-weight: 500; margin-top: 20px; margin-bottom: 8px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
th {{ background-color: #f9fafb; font-weight: 600; color: #4b5563; text-transform: uppercase; font-size: 0.75rem; }}
.bg-green-100 {{ background-color: #D1FAE5; }} .bg-green-200 {{ background-color: #A7F3D0; }} .bg-green-300 {{ background-color: #6EE7B7; }} .bg-green-400 {{ background-color: #34D399; }} .bg-green-500 {{ background-color: #10B981; }}
.bg-red-100 {{ background-color: #FEE2E2; }} .bg-red-200 {{ background-color: #FECACA; }} .bg-red-300 {{ background-color: #FCA5A5; }} .bg-red-400 {{ background-color: #F87171; }} .bg-red-500 {{ background-color: #EF4444; }}
.bg-gray-300 {{ background-color: #D1D5DB; }} .bg-gray-200 {{ background-color: #E5E7EB; }}
.text-white {{ color: #ffffff; }} .text-gray-800 {{ color: #1f2937; }}
.section-content {{ transition: max-height 0.4s ease-in-out, opacity 0.3s ease-in-out; overflow: hidden; max-height: 20000px; opacity: 1; }}
.section-collapsed {{ max-height: 0; opacity: 0; margin-top:0; margin-bottom:0; padding-top:0; padding-bottom:0; }}
.chart-container {{ width: 100%; margin-bottom: 20px; }} .chart-container > div {{ width: 100% !important; }}
</style></head><body class="bg-gray-100 p-4 md:p-8"><div class="container">
<div class="mb-6 text-center"><h1 class="bg-gradient-to-r from-blue-600 via-sky-500 to-cyan-400 text-transparent bg-clip-text">Daily Financial Market Snapshot</h1>
<p class="text-gray-600 mt-1">Generated on: {TODAY_DT.strftime('%Y-%m-%d %H:%M:%S')}</p></div>
<h2 onclick="toggleSection('equities-section')"><span><i class="fas fa-chart-line mr-2"></i>I. Equities</span><i class="fas fa-chevron-down ml-auto chevron-icon"></i></h2>
<div id="equities-section" class="section-content">
"""
    html_output = html_head; spy_chart_data_df = None; us_equity_data_list = []
    us_equity_order = ["S&P 500", "QQQ (Nasdaq 100)", "Russell 2000"]
    remaining_us_equities = sorted([name for name in US_EQUITY_TICKERS.keys() if name not in us_equity_order])
    full_us_equity_order = us_equity_order + remaining_us_equities
    for name in full_us_equity_order:
        ticker = US_EQUITY_TICKERS[name]
        hist_data_df = get_yfinance_data(ticker, THREE_MONTHS_AGO_FOR_FETCH, TODAY)
        if ticker == "SPY" and not hist_data_df.empty: spy_chart_data_df = hist_data_df.copy()
        perf = calculate_yfinance_performance(ticker, hist_data_df)
        us_equity_data_list.append({"Asset": name, "Ticker": ticker, "Current Level": hist_data_df['Close'].iloc[-1].item() if not hist_data_df.empty else "N/A", "Past Day Change (%)": perf['Day'], "Past Week Change (%)": perf['Week'], "Past Month Change (%)": perf['Month']})
    us_equities_df = pd.DataFrame(us_equity_data_list)
    if spy_chart_data_df is not None: html_output += f"<div class='chart-container'>{generate_plotly_chart(spy_chart_data_df, 'S&P 500 (SPY) - 30 Day Performance', days_history=30)}</div>"
    html_output += create_html_table(us_equities_df, "A. US Indices & Sectors")

    sentiment_data_list = []
    for name, ticker in US_SENTIMENT_TICKERS.items():
        hist_data_df = get_yfinance_data(ticker, THREE_MONTHS_AGO_FOR_FETCH, TODAY)
        perf = calculate_yfinance_performance(ticker, hist_data_df)
        sentiment_data_list.append({"Indicator": name, "Ticker": ticker, "Current Level": hist_data_df['Close'].iloc[-1].item() if not hist_data_df.empty else "N/A", "Past Day Change (%)": perf['Day'], "Past Week Change (%)": perf['Week'], "Past Month Change (%)": perf['Month']})
    sentiment_df = pd.DataFrame(sentiment_data_list); html_output += create_html_table(sentiment_df, "B. Market Sentiment Indicators")

    all_global_hist_data = {}; global_equity_data_list = []
    global_equity_order = ["All Country World Index (ACWI)", "Developed Markets ex-NA (EFA)", "Emerging Markets (EEM)"]
    remaining_global_equities = sorted([name for name in GLOBAL_EQUITY_TICKERS.keys() if name not in global_equity_order])
    full_global_equity_order = global_equity_order + remaining_global_equities
    for name in full_global_equity_order:
        ticker = GLOBAL_EQUITY_TICKERS[name]
        hist_data_df = get_yfinance_data(ticker, THREE_MONTHS_AGO_FOR_FETCH, TODAY)
        if not hist_data_df.empty: all_global_hist_data[ticker] = hist_data_df.copy()
        perf_data = calculate_yfinance_performance(ticker, hist_data_df)
        global_equity_data_list.append({"Asset": name, "Ticker": ticker, "Current Level": hist_data_df['Close'].iloc[-1].item() if not hist_data_df.empty else "N/A", "Past Day Change (%)": perf_data['Day'], "Past Week Change (%)": perf_data['Week'], "Past Month Change (%)": perf_data['Month']})
    global_equities_df = pd.DataFrame(global_equity_data_list); top_performer_chart_html = ""
    if not global_equities_df.empty:
        temp_df = global_equities_df.copy(); temp_df['Past Month Change (%)'] = pd.to_numeric(temp_df['Past Month Change (%)'], errors='coerce')
        monthly_perf = temp_df['Past Month Change (%)'].dropna()
        if not monthly_perf.empty:
            top_idx = monthly_perf.idxmax() if monthly_perf.index.is_unique else monthly_perf.nlargest(1).index[0]
            if top_idx in temp_df.index:
                top_series = temp_df.loc[top_idx]; top_ticker = top_series['Ticker']; top_name = top_series['Asset']
                if top_ticker in all_global_hist_data:
                    chart_title = f"{top_name} ({top_ticker}) - 30 Day Performance"
                    top_performer_chart_html = generate_plotly_chart(all_global_hist_data[top_ticker], chart_title, days_history=30)
                else: top_performer_chart_html = f"<p class='text-sm text-orange-600'>Hist data for {top_name} not found.</p>"
            else: top_performer_chart_html = "<p class='text-sm text-orange-600'>Top performer index error.</p>"
        else: top_performer_chart_html = "<p class='text-sm text-orange-600'>No valid monthly perf data.</p>"
    else: top_performer_chart_html = "<p class='text-sm text-orange-600'>Global equities data empty.</p>"
    if top_performer_chart_html: html_output += f"<div class='chart-container'>{top_performer_chart_html}</div>"
    html_output += create_html_table(global_equities_df, "C. Global Equity Indices (Proxied by ETFs)")
    html_output += '<h4 class="text-lg font-semibold mb-1 mt-6">D. Top/Bottom 5 Global Equity Performers</h4>\n'
    temp_perf_df = global_equities_df.copy()
    for period_col in ["Past Day Change (%)", "Past Week Change (%)", "Past Month Change (%)"]:
        top_p, bottom_p = get_top_bottom_performers(temp_perf_df, period_col)
        period_name = period_col.split(" ")[1]
        html_output += f'<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">\n'
        html_output += f'<div><h4 class="text-md font-medium mb-1">Past {period_name} Top 5</h4>{create_html_table(top_p[["Asset", period_col]], f"Top{period_name}Global", apply_heatmap=False)}</div>\n'
        html_output += f'<div><h4 class="text-md font-medium mb-1">Past {period_name} Bottom 5</h4>{create_html_table(bottom_p[["Asset", period_col]], f"Bottom{period_name}Global", apply_heatmap=False)}</div>\n</div>\n'

    html_output += """</div><h2 onclick="toggleSection('fixed-income-section')"><span><i class="fas fa-university mr-2"></i>II. Fixed Income</span><i class="fas fa-chevron-down ml-auto chevron-icon"></i></h2><div id="fixed-income-section" class="section-content">"""
    fixed_income_data = []
    full_fixed_income_order = ["MOVE Index", "3-Month T-Bill Yield", "2-Year T-Note Yield", "10-Year T-Bond Yield", "30-Year T-Bond Yield", "High Grade Bonds", "High Yield Bonds"]
    for name in full_fixed_income_order:
        current_val, day_chg, week_chg, month_chg = "N/A", "N/A", "N/A", "N/A"
        if name in FRED_FIXED_INCOME_SERIES:
            s_id = FRED_FIXED_INCOME_SERIES[name]; s_hist = get_fred_data(s_id, FRED_API_KEY, THREE_MONTHS_AGO_FOR_FETCH, TODAY)
            if not s_hist.empty: current_val=s_hist.iloc[-1].item(); perf=calculate_fred_performance(s_hist); day_chg,week_chg,month_chg = perf['Day'],perf['Week'],perf['Month']
        elif name in YFINANCE_FIXED_INCOME_TICKERS:
            tckr = YFINANCE_FIXED_INCOME_TICKERS[name]; h_df = get_yfinance_data(tckr, THREE_MONTHS_AGO_FOR_FETCH, TODAY)
            if not h_df.empty: current_val=h_df['Close'].iloc[-1].item(); perf=calculate_yfinance_performance(tckr,h_df); day_chg,week_chg,month_chg = perf['Day'],perf['Week'],perf['Month']
        fixed_income_data.append({"Asset":name, "Current Level":current_val, "Past Day Change (bps/%)":day_chg, "Past Week Change (bps/%)":week_chg, "Past Month Change (bps/%)":month_chg})
    fixed_income_df = pd.DataFrame(fixed_income_data); html_output += create_html_table(fixed_income_df, "A. Treasury Yields & Corporate Bonds")

    html_output += """</div><h2 onclick="toggleSection('commodities-section')"><span><i class="fas fa-boxes mr-2"></i>III. Commodities</span><i class="fas fa-chevron-down ml-auto chevron-icon"></i></h2><div id="commodities-section" class="section-content">"""
    commodity_data = []
    comm_order = ["S&P GSCI", "WTI Crude Oil", "Gold"]; rem_comm = sorted([n for n in COMMODITY_TICKERS.keys() if n not in comm_order]); full_comm_order = comm_order + rem_comm
    for name in full_comm_order:
        tckr = COMMODITY_TICKERS[name]; curr_price, d_perf, w_perf, m_perf = "N/A", "N/A", "N/A", "N/A"
        if not tckr.startswith("N/A"):
            h_df = get_yfinance_data(tckr, THREE_MONTHS_AGO_FOR_FETCH, TODAY)
            if not h_df.empty: curr_price=h_df['Close'].iloc[-1].item(); perf=calculate_yfinance_performance(tckr,h_df); d_perf,w_perf,m_perf = perf['Day'],perf['Week'],perf['Month']
        commodity_data.append({"Commodity":name, "Current Price":curr_price, "Past Day Change (%)":d_perf, "Past Week Change (%)":w_perf, "Past Month Change (%)":m_perf})
    comm_df = pd.DataFrame(commodity_data); html_output += create_html_table(comm_df, "A. Commodity Prices")

    html_output += """</div><h2 onclick="toggleSection('crypto-section')"><span><i class="fab fa-bitcoin mr-2"></i>IV. Cryptocurrency</span> <i class="fas fa-chevron-down ml-auto chevron-icon"></i></h2><div id="crypto-section" class="section-content">"""
    crypto_list = []
    for name, tckr in CRYPTO_TICKERS.items():
        h_df = get_yfinance_data(tckr, THREE_MONTHS_AGO_FOR_FETCH, TODAY); curr_price,d_perf,w_perf,m_perf = "N/A","N/A","N/A","N/A"
        if not h_df.empty: curr_price=h_df['Close'].iloc[-1].item(); perf=calculate_yfinance_performance(tckr,h_df); d_perf,w_perf,m_perf = perf['Day'],perf['Week'],perf['Month']
        crypto_list.append({"Asset":name, "Ticker":tckr, "Current Price":curr_price, "Past Day Change (%)":d_perf, "Past Week Change (%)":w_perf, "Past Month Change (%)":m_perf})
    crypto_df_tbl = pd.DataFrame(crypto_list); html_output += create_html_table(crypto_df_tbl, "A. Major Cryptocurrencies")

    html_output += """</div><h2 onclick="toggleSection('currencies-section')"><span><i class="fas fa-money-bill-wave mr-2"></i>V. Currencies (Against USD)</span><i class="fas fa-chevron-down ml-auto chevron-icon"></i></h2><div id="currencies-section" class="section-content">"""
    curr_data = []
    curr_order = ["DXY (US Dollar Index)"]; rem_curr = sorted([n for n in CURRENCY_TICKERS.keys() if n not in curr_order]); full_curr_order = curr_order + rem_curr
    for name in full_curr_order:
        tckr = CURRENCY_TICKERS[name]; h_df = get_yfinance_data(tckr, THREE_MONTHS_AGO_FOR_FETCH, TODAY)
        curr_rate_val,d_perf,w_perf,m_perf = "N/A","N/A","N/A","N/A"
        if not h_df.empty: perf_res, curr_rate = get_currency_performance(tckr, h_df); curr_rate_val=curr_rate; d_perf,w_perf,m_perf=perf_res['Day'],perf_res['Week'],perf_res['Month']
        curr_data.append({"Currency":name, "Ticker":tckr, "Current Rate":curr_rate_val, "Past Day Change (%)":d_perf, "Past Week Change (%)":w_perf, "Past Month Change (%)":m_perf})
    curr_df_tbl = pd.DataFrame(curr_data); html_output += create_html_table(curr_df_tbl, "A. FX Rates vs USD")
    html_output += '<h4 class="text-lg font-semibold mb-1 mt-6">B. Top/Bottom 5 Currency Performers</h4>\n'
    temp_curr_perf_df = curr_df_tbl.copy()
    for period_col in ["Past Day Change (%)", "Past Week Change (%)", "Past Month Change (%)"]:
        top_c, bottom_c = get_top_bottom_performers(temp_curr_perf_df, period_col)
        period_name = period_col.split(" ")[1]
        html_output += f'<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">\n'
        html_output += f'<div><h4 class="text-md font-medium mb-1">Past {period_name} Top 5</h4>{create_html_table(top_c[["Currency", period_col]], f"Top{period_name}Curr", apply_heatmap=False)}</div>\n'
        html_output += f'<div><h4 class="text-md font-medium mb-1">Past {period_name} Bottom 5</h4>{create_html_table(bottom_c[["Currency", period_col]], f"Bottom{period_name}Curr", apply_heatmap=False)}</div>\n</div>\n'
    html_output += """</div></div><script>
function toggleSection(id){const element=document.getElementById(id);const sectionHeader=element.previousElementSibling;const chevron=sectionHeader.querySelector('.chevron-icon');
if(element.classList.contains('section-collapsed')){element.classList.remove('section-collapsed');chevron.classList.remove('rotate-90');}else{element.classList.add('section-collapsed');chevron.classList.add('rotate-90');}}
</script></body></html>"""
    return html_output

if __name__ == "__main__":
    pio.templates.default = "plotly_white"
    print("Generating financial market report...")
    report = generate_morning_report()
    # Updated output filename to reflect the new script name for consistency
    output_filename = f"market_snapshot_{TODAY_DT.strftime('%Y%m%d')}.html" 
    with open(output_filename, "w", encoding='utf-8') as f: f.write(report)
    print(f"\nReport saved to {output_filename}")
    try: import webbrowser; webbrowser.open('file://' + os.path.realpath(output_filename))
    except Exception as e: print(f"Could not automatically open the report in a browser: {e}")