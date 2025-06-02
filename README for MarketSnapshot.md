################################################################################
# README for Daily_Financial_Market_Snapshot_v3a.py
################################################################################

--------------------------------------------------------------------------------
Purpose:
--------------------------------------------------------------------------------
This Python script generates a daily HTML report summarizing key financial market
data. It fetches data from Yahoo Finance (yfinance) for equities, commodities,
cryptocurrencies, and currencies, and from the St. Louis FRED API for fixed
income yields. The report includes current levels, percentage changes (or basis
point changes for yields) over various periods (day, week, month), top/bottom
performers, and interactive 30-day price charts for selected assets.

--------------------------------------------------------------------------------
Key Features:
--------------------------------------------------------------------------------
1.  **Data Aggregation:** Collects data from multiple sources (Yahoo Finance, FRED).
2.  **Multi-Asset Class Coverage:**
    *   US Equities (Indices & Sectors)
    *   Market Sentiment Indicators (VIX, VXN)
    *   Global Equities (Country/Region ETFs)
    *   Fixed Income (Treasury Yields, Corporate Bond ETFs, MOVE Index)
    *   Commodities (Futures & Spot Prices)
    *   Cryptocurrencies (Bitcoin, Ethereum, Solana)
    *   Currencies (FX Rates against USD, DXY)
3.  **Performance Calculation:** Calculates day, week, and month percentage changes
    (or absolute basis point changes for yields).
4.  **Top/Bottom Performers:** Identifies top 5 and bottom 5 performers for
    global equities and currencies over different timeframes.
5.  **Interactive Charts:** Generates 30-day price charts using Plotly for:
    *   S&P 500 (SPY)
    *   Top Monthly Global Equity Performer
6.  **HTML Report Generation:** Outputs a styled, collapsible HTML report using
    Tailwind CSS for easy viewing. Heatmaps are used to visualize performance
    in tables.
7.  **Configuration:** Uses environment variables for API keys (e.g., FRED_API_KEY).

--------------------------------------------------------------------------------
Core Dependencies:
--------------------------------------------------------------------------------
-   pandas: For data manipulation and analysis.
-   yfinance: For fetching stock, ETF, commodity, crypto, and currency data.
-   requests: For making HTTP requests to the FRED API.
-   plotly: For generating interactive charts.
-   os: For environment variable access.
-   json: For parsing JSON responses from FRED.
-   datetime, timedelta: For date and time calculations.

Ensure these are installed in your Python environment (e.g., `pip install pandas yfinance requests plotly`).

--------------------------------------------------------------------------------
Script Structure & Workflow:
--------------------------------------------------------------------------------
1.  **Configuration:**
    *   Sets up API keys (FRED_API_KEY).
    *   Defines date constants (TODAY, historical dates for data fetching).
    *   Defines dictionaries of tickers and series IDs for various asset classes.

2.  **Helper Functions:**
    *   `get_yfinance_data()`: Fetches and processes historical data from Yahoo Finance.
        *   Normalizes datetime index to date part only.
    *   `calculate_yfinance_performance()`: Calculates % change for yfinance data.
    *   `get_fred_data()`: Fetches and processes time series data from FRED.
        *   Normalizes datetime index to date part only.
    *   `calculate_fred_performance()`: Calculates absolute (bps) change for FRED data.
    *   `get_currency_performance()`: Calculates % change for currency pairs.
    *   `get_top_bottom_performers()`: Identifies top/bottom N performers from a DataFrame.
    *   `get_heatmap_class()`: Determines Tailwind CSS classes for heatmap cells.
    *   `create_html_table()`: Generates an HTML table from a Pandas DataFrame with
        optional heatmapping.
    *   `generate_plotly_chart()`: Generates an HTML string for an interactive Plotly chart.
        *   Ensures y-data is passed as a list to `go.Scatter`.

3.  **`generate_morning_report()` - Main Function:**
    *   Initializes HTML head and styling.
    *   Iterates through each asset class:
        *   Fetches historical data using helper functions.
        *   Calculates performance metrics.
        *   For SPY and the top global equity performer, historical data is stored
          to generate Plotly charts.
        *   Formats data into Pandas DataFrames.
        *   Appends generated HTML (charts and tables) to the main HTML output string.
    *   Adds JavaScript for collapsible sections.
    *   Returns the complete HTML report string.

4.  **`if __name__ == "__main__":` Block:**
    *   Calls `generate_morning_report()`.
    *   Saves the report to an HTML file named `morning_report_{YYYYMMDD}_v3a.html`.
    *   Attempts to open the generated report in the default web browser.

--------------------------------------------------------------------------------
Architectural Considerations & Potential Issues for Future Development/AI:
--------------------------------------------------------------------------------
1.  **API Rate Limits & Reliability:**
    *   **Yahoo Finance (yfinance):** Can be unreliable or change its unofficial API.
      Heavy usage might lead to temporary blocks. No explicit rate limiting, but
      treat it as a best-effort service.
    *   **FRED API:** Has rate limits (check St. Louis Fed website). The current script
      makes a small number of requests, so it's unlikely to hit limits with daily runs.
    *   **Mitigation:** Implement robust error handling, retries with backoff for API calls.
      Consider caching data locally for short periods if run frequently.

2.  **Date/Timezone Handling:**
    *   The script currently converts `TODAY` to a `pd.Timestamp` for date arithmetic and
      normalizes all datetime indexes to midnight (date part only) to ensure consistency.
    *   `THREE_MONTHS_AGO_FOR_FETCH` is a standard `datetime.datetime` object passed to
      `yf.download`. `TODAY` (as `pd.Timestamp`) is used as the `end_date`.
    *   This setup works, but future changes involving more complex time-sensitive
      calculations (e.g., intraday data, specific market open/close times) would
      require more rigorous timezone management (e.g., using `pytz` or Python 3.9+ `zoneinfo`,
      and ensuring all timestamps are timezone-aware or consistently naive UTC).

3.  **Error Handling for Data Fetching:**
    *   `get_yfinance_data` and `get_fred_data` have basic try-except blocks and print
      warnings for missing data or errors, returning empty DataFrames/Series.
    *   The main report generation loop proceeds even if some assets fail to load,
      resulting in "N/A" values.
    *   **Future AI:** Could enhance this to provide more granular error reporting in
      the HTML output itself (e.g., "Failed to load SPY data") or implement more
      sophisticated fallback mechanisms.

4.  **Hardcoded Ticker Lists:**
    *   `US_EQUITY_TICKERS`, `GLOBAL_EQUITY_TICKERS`, etc., are hardcoded Python dictionaries.
    *   **Future AI:** If these lists need to be dynamic or user-configurable, consider
      moving them to external configuration files (JSON, YAML, CSV).

5.  **HTML Generation:**
    *   HTML is constructed by concatenating f-strings. This is functional but can
      become unwieldy for very complex layouts.
    *   **Future AI:** For significant UI changes, consider using a templating engine
      (e.g., Jinja2) for better separation of logic and presentation. This would
      make the HTML structure easier to manage and modify.

6.  **Plotly Chart Configuration:**
    *   Chart styling is basic. `generate_plotly_chart` has fixed parameters for `days_history`.
    *   `include_plotlyjs='cdn'` is used, which means an internet connection is needed
      to render charts initially. The Plotly.js library is fetched from a CDN.
    *   **Future AI:** Could make chart parameters (days, type, colors) configurable.
      For offline use or controlled environments, Plotly.js could be bundled or
      self-hosted. The current `plotly-3.0.1.min.js` loaded via CDN works with the
      `.tolist()` fix for y-data.

7.  **Performance Calculation Logic:**
    *   `calculate_yfinance_performance` and other performance functions rely on slicing
      DataFrames based on date offsets from `TODAY`. This assumes that historical
      data points exist reasonably close to these offset dates. For thinly traded
      assets or assets with missing data, the "week ago" or "month ago" price might
      be from an earlier date if no data point is found exactly 7 or 30 days prior.
      The current logic takes the *last available price on or before* that target date.
    *   This is generally acceptable for daily snapshots but could be refined if more
      precise "N-trading-days-ago" logic is required.

8.  **Scalability of Data Processing:**
    *   The script processes tickers sequentially. For a vastly larger number of tickers,
      fetching and processing could become slow.
    *   **Future AI:** Could explore asynchronous data fetching (`asyncio` with `aiohttp` for FRED
      and potentially adapting `yfinance` or using alternative async libraries if available)
      to speed up the data collection phase.

9.  **VS Code Pylance Import Resolution:**
    *   If Pylance reports "Import X could not be resolved" but the script runs, it means
      the VS Code workspace is not using the same Python interpreter/environment that
      the script is being executed with (and where the library is installed).
    *   This is an IDE configuration issue, not a script bug. The fix is to select the
      correct Python interpreter in VS Code (Ctrl+Shift+P -> "Python: Select Interpreter").

10. **`.item()` vs. `.iloc[0]` for Single Value Extraction:**
    *   The script uses `series.iloc[-1].item()` to get the scalar value from the last
      element of a single-column DataFrame's column (which is a Series). This is fine
      as long as the selection indeed results in a Series with one element.
    *   `series.iloc[-1]` would also work if direct assignment of the scalar is needed,
      as Pandas often handles this conversion. `.item()` is more explicit for
      "get the single Python scalar value".

By being aware of these points, a future AI (or human developer) can more effectively
maintain, debug, and extend this script.