# Interactive Stock Comparison Dashboard

A Streamlit + Plotly dashboard inspired by the Kean University “At-a-Glance” dashboard layout. It compares Apple (AAPL), Microsoft (MSFT), and NVIDIA (NVDA) by default, with options to add Alphabet, Amazon, Meta, and Tesla.

## Visualizations

1. Relative/indexed performance (start date = 100)
2. Adjusted closing price
3. Daily percentage returns
4. Daily return distribution (box plot)
5. Rolling 20-trading-day annualized volatility
6. Total return over the selected period
7. Daily trading volume

The company multi-select and date range are shared filters that update all charts and the comparison table. Summary indicators are shown separately and do not count toward the visualization requirement.

## Run locally

Python 3.10+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows
pip install -r requirements.txt
streamlit run app.py
```

The app fetches market data at runtime through `yfinance` and caches it for 15 minutes. Internet access is required. Yahoo Finance data may be delayed, adjusted, or unavailable at times.

## Deploy to Streamlit Community Cloud

1. Create a GitHub repository and upload `app.py`, `requirements.txt`, `README.md`, and the `.streamlit/config.toml` file (preserving the `.streamlit` folder).
2. Sign in at https://share.streamlit.io/ with GitHub.
3. Choose **Create app**, select the repository and branch, and set the main file path to `app.py`.
4. Deploy. Streamlit installs the packages from `requirements.txt`.
5. Open the generated public app URL and test the company and date filters.

I can prepare the deployable source package here, but I cannot publish it to your personal hosting account without access/authorization to that service.

## Notes

- Adjusted closing prices are used for return calculations to account for splits and dividends where available.
- “Latest data date” is the latest date returned for the selected companies and date range, not necessarily today's date (markets close, weekends, holidays, and feed delays apply).
- The dashboard is educational and is not investment advice.
