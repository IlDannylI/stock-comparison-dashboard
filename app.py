import datetime as dt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="Stock Market Comparison",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Kean-inspired layout: dark institutional header, compact shared filters,
# broad central comparisons, and a clean light dashboard canvas.
NAVY = "#1D3156"
BLUE = "#3977C8"
LIGHT_BLUE = "#5B9BE3"
GOLD = "#E8BD32"
GREEN = "#269B77"
RED = "#D9535D"
PALETTE = [BLUE, LIGHT_BLUE, GOLD, GREEN, RED, "#7868A6", "#E28C45"]

st.markdown(
    f"""
    <style>
      /* Force a consistent light theme even if Streamlit's browser theme is dark. */
      html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"],
      [data-testid="stMainBlockContainer"], .stApp {{
        background: #ffffff !important;
        color: #172033 !important;
      }}
      [data-testid="stMain"] p, [data-testid="stMain"] label,
      [data-testid="stMain"] h1, [data-testid="stMain"] h2,
      [data-testid="stMain"] h3, [data-testid="stMain"] h4,
      [data-testid="stMain"] span, [data-testid="stMain"] li,
      [data-testid="stMain"] [data-testid="stMarkdownContainer"] {{
        color: #172033;
      }}
      .dashboard-header {{
        background: {NAVY} !important; color: #ffffff !important;
        padding: 17px 24px; border-radius: 2px; margin-bottom: 14px;
        display:flex; align-items:center; justify-content:space-between; gap:20px;
      }}
      .dashboard-header .brand {{ color: #ffffff !important; font-size: 1.1rem; letter-spacing: .06em; opacity: .95; }}
      .dashboard-header .title {{ color: #ffffff !important; font-family: Georgia, serif; font-size: 1.65rem; }}
      .dashboard-header .title span {{color: #ffffff !important;display: inline-block;}}
      .subtle {{ color: #64748b !important; font-size: .9rem; }}
      div[data-testid="stMetric"] {{
        border: 1px solid #d7dee8; border-radius: 8px; padding: 12px 14px;
        background: #f8fafc !important; color: #172033 !important;
      }}
      div[data-testid="stMetric"] label,
      div[data-testid="stMetric"] [data-testid="stMetricLabel"],
      div[data-testid="stMetric"] [data-testid="stMetricValue"],
      div[data-testid="stMetric"] [data-testid="stMetricDelta"] {{
        color: #172033 !important;
      }}
      [data-testid="stSidebar"] {{
        background: #f1f4f8 !important;
      }}
      [data-testid="stSidebar"] p, [data-testid="stSidebar"] label,
      [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
      [data-testid="stSidebar"] h3, [data-testid="stSidebar"] span,
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
        color: #172033 !important;
      }}
      [data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea,
      [data-testid="stSidebar"] [data-baseweb="select"] * {{
        color: #172033 !important;
        background-color: #ffffff !important;
      }}
      [data-testid="stSidebar"] button {{
        background: #26364f !important; color: #ffffff !important;
        border: 1px solid #26364f !important;
      }}
      [data-testid="stSidebar"] button * {{ color: #ffffff !important; }}
      [data-testid="stToolbar"] {{ background: #ffffff; }}
      [data-testid="stHeader"] {{ background: #ffffff !important; }}
      h2, h3 {{ color: #172033 !important; }}
    </style>
<div class="dashboard-header">
  <div class="brand">
    <b>STOCK MARKET ANALYTICS</b><br/>
    KEAN UNIVERSITY
  </div>
  <div class="title">
    Stock Performance — At a Glance<br/>
    <span style="font-family: Arial, sans-serif; 
    font-size: 14px; 
    color: #FFFFFF !important;">
      Prepared by: Danny Munoz | Course: CPS 5745
    </span>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"]
COMPANY_NAMES = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "META": "Meta Platforms",
    "TSLA": "Tesla",
}

@st.cache_data(ttl=900, show_spinner=False)
def load_prices(tickers, start_date, end_date):
    # yfinance end date is exclusive; add a day so the selected end date is included.
    end_exclusive = pd.Timestamp(end_date) + pd.Timedelta(days=1)
    raw = yf.download(
        tickers=list(tickers),
        start=pd.Timestamp(start_date).strftime("%Y-%m-%d"),
        end=end_exclusive.strftime("%Y-%m-%d"),
        auto_adjust=False,
        group_by="ticker",
        progress=False,
        threads=True,
    )
    if raw.empty:
        return pd.DataFrame()

    frames = []
    fields = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    for ticker in tickers:
        try:
            if isinstance(raw.columns, pd.MultiIndex):
                # yfinance commonly returns ticker first for group_by="ticker".
                if ticker in raw.columns.get_level_values(0):
                    part = raw[ticker].copy()
                elif ticker in raw.columns.get_level_values(-1):
                    part = raw.xs(ticker, axis=1, level=-1).copy()
                else:
                    continue
            else:
                if len(tickers) != 1:
                    continue
                part = raw.copy()
            available = [f for f in fields if f in part.columns]
            if "Close" not in available:
                continue
            part = part[available].copy()
            part["Ticker"] = ticker
            part["Company"] = COMPANY_NAMES.get(ticker, ticker)
            part.index.name = "Date"
            frames.append(part.reset_index())
        except (KeyError, ValueError, TypeError):
            continue

    if not frames:
        return pd.DataFrame()
    data = pd.concat(frames, ignore_index=True)
    data["Date"] = pd.to_datetime(data["Date"]).dt.tz_localize(None)
    data = data.sort_values(["Ticker", "Date"])
    # Use adjusted close for return calculations to account for splits/dividends.
    data["Adjusted"] = data["Adj Close"] if "Adj Close" in data else data["Close"]
    data["Daily Return"] = data.groupby("Ticker")["Adjusted"].pct_change() * 100
    data["Indexed Performance"] = data.groupby("Ticker")["Adjusted"].transform(
        lambda s: (s / s.dropna().iloc[0] * 100) if s.notna().any() else s
    )
    data["20-Day Volatility"] = data.groupby("Ticker")["Daily Return"].transform(
        lambda s: s.rolling(20, min_periods=10).std() * np.sqrt(252)
    )
    data["20-Day Average"] = data.groupby("Ticker")["Adjusted"].transform(
        lambda s: s.rolling(20, min_periods=1).mean()
    )
    return data

def money(v):
    return f"${v:,.2f}" if pd.notna(v) else "—"

with st.sidebar:
    st.header("Dashboard filters")
    selected_tickers = st.multiselect(
        "Companies",
        options=DEFAULT_TICKERS,
        default=["AAPL", "MSFT", "NVDA"],
        format_func=lambda t: f"{t} — {COMPANY_NAMES[t]}",
        help="The same company selection updates every visualization.",
    )
    today = dt.date.today()
    default_start = today - dt.timedelta(days=365)
    date_range = st.date_input(
        "Date range",
        value=(default_start, today),
        min_value=dt.date(2015, 1, 1),
        max_value=today,
        help="The same date range updates every visualization.",
    )
    st.caption("Data source: Yahoo Finance via yfinance")
    st.caption("Refresh interval: cached for 15 minutes")
    refresh = st.button("Refresh latest data", use_container_width=True)
    if refresh:
        st.cache_data.clear()
        st.rerun()

if len(selected_tickers) < 2:
    st.warning("Select at least two companies to compare them.")
    st.stop()
if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.info("Choose both a start date and an end date.")
    st.stop()
start_date, end_date = date_range
if start_date > end_date:
    st.error("The start date must be on or before the end date.")
    st.stop()

with st.spinner("Loading the latest available market data…"):
    df = load_prices(tuple(selected_tickers), start_date.isoformat(), end_date.isoformat())

if df.empty:
    st.error("No stock data was returned. Try another date range or refresh the data.")
    st.stop()

df = df.dropna(subset=["Adjusted"]).copy()
if df.empty:
    st.error("There are no valid adjusted closing prices in this date range.")
    st.stop()

latest = df.sort_values("Date").groupby("Ticker", as_index=False).tail(1)
first_last = df.groupby("Ticker").agg(
    first=("Adjusted", "first"), last=("Adjusted", "last"),
    first_date=("Date", "min"), last_date=("Date", "max")
)
first_last["Total Return"] = (first_last["last"] / first_last["first"] - 1) * 100
first_last["Company"] = first_last.index.map(COMPANY_NAMES)

# Summary indicators are intentionally separate from the required visualizations.
m1, m2, m3, m4 = st.columns(4)
m1.metric("Companies selected", f"{len(selected_tickers)}")
m2.metric("Trading days", f"{df['Date'].nunique():,}")
best = first_last["Total Return"].idxmax()
m3.metric("Top performer", best, f"{first_last.loc[best, 'Total Return']:+.2f}%")
m4.metric("Latest data date", df["Date"].max().strftime("%b %d, %Y"))
st.caption("Returns use adjusted closing prices. Market data can be delayed or revised; this dashboard is for educational use, not investment advice.")

def chart_layout(fig, height=360):
    fig.update_layout(
        height=height, margin=dict(l=12, r=12, t=50, b=12),
        paper_bgcolor="white", plot_bgcolor="white",
        legend_title_text="", hovermode="x unified",
        font=dict(family="Arial, sans-serif", color="#172033"),
    )
    fig.update_xaxes(showgrid=False, linecolor="#d9dee7")
    fig.update_yaxes(gridcolor="#e8ebf0", zerolinecolor="#d9dee7")
    return fig

company_order = selected_tickers
color_map = {t: PALETTE[i % len(PALETTE)] for i, t in enumerate(company_order)}
st.subheader("Performance comparisons")

# 1. Indexed performance
fig1 = px.line(
    df, x="Date", y="Indexed Performance", color="Ticker",
    color_discrete_map=color_map,
    labels={"Indexed Performance": "Growth of $100 (index)", "Date": "Date", "Ticker": "Company"},
    title="1. Relative performance (start date = 100)",
    hover_data={"Company": True, "Adjusted": ":.2f", "Indexed Performance": ":.2f"},
)
fig1.add_hline(y=100, line_dash="dot", line_color="#8993a4")
st.plotly_chart(chart_layout(fig1), use_container_width=True)

left, right = st.columns(2)
# 2. Adjusted closing price
fig2 = px.line(
    df, x="Date", y="Adjusted", color="Ticker", color_discrete_map=color_map,
    labels={"Adjusted": "Adjusted close (USD)", "Date": "Date", "Ticker": "Company"},
    title="2. Adjusted closing price",
    hover_data={"Company": True, "Adjusted": ":$,.2f"},
)
left.plotly_chart(chart_layout(fig2), use_container_width=True)

# 3. Daily returns
returns = df.dropna(subset=["Daily Return"])
fig3 = px.line(
    returns, x="Date", y="Daily Return", color="Ticker", color_discrete_map=color_map,
    labels={"Daily Return": "Daily return (%)", "Date": "Date", "Ticker": "Company"},
    title="3. Daily percentage returns",
)
fig3.add_hline(y=0, line_color="#8993a4", line_dash="dot")
right.plotly_chart(chart_layout(fig3), use_container_width=True)

left, right = st.columns(2)
# 4. Return distribution
fig4 = px.box(
    returns, x="Ticker", y="Daily Return", color="Ticker", points=False,
    color_discrete_map=color_map,
    labels={"Daily Return": "Daily return (%)", "Ticker": "Company"},
    title="4. Daily return distribution",
)
left.plotly_chart(chart_layout(fig4), use_container_width=True)

# 5. Annualized rolling volatility
vol = df.dropna(subset=["20-Day Volatility"])
fig5 = px.line(
    vol, x="Date", y="20-Day Volatility", color="Ticker", color_discrete_map=color_map,
    labels={"20-Day Volatility": "Annualized volatility (%)", "Date": "Date", "Ticker": "Company"},
    title="5. Rolling 20-trading-day volatility (annualized)",
)
right.plotly_chart(chart_layout(fig5), use_container_width=True)

# 6. Total return bar chart
perf = first_last.reset_index(names="Ticker").sort_values("Total Return", ascending=False)
fig6 = px.bar(
    perf, x="Ticker", y="Total Return", color="Ticker", color_discrete_map=color_map,
    text=perf["Total Return"].map(lambda x: f"{x:+.1f}%"),
    labels={"Total Return": "Total return over selected period (%)", "Ticker": "Company"},
    title="6. Total return over selected period",
)
fig6.update_traces(textposition="outside", cliponaxis=False)
fig6.add_hline(y=0, line_color="#8993a4")
st.plotly_chart(chart_layout(fig6, 340), use_container_width=True)

# 7. Trading volume
if "Volume" in df.columns and df["Volume"].notna().any():
    fig7 = px.line(
        df, x="Date", y="Volume", color="Ticker", color_discrete_map=color_map,
        labels={"Volume": "Shares traded", "Date": "Date", "Ticker": "Company"},
        title="7. Daily trading volume",
    )
    st.plotly_chart(chart_layout(fig7, 340), use_container_width=True)

st.subheader("Company comparison table")
table = first_last.reset_index(names="Ticker")
table["Latest adjusted close"] = table["Ticker"].map(
    latest.set_index("Ticker")["Adjusted"].to_dict()
)
table["Total return (%)"] = table["Total Return"]
table["Start date"] = table["first_date"].dt.strftime("%Y-%m-%d")
table["End date"] = table["last_date"].dt.strftime("%Y-%m-%d")
table = table[["Ticker", "Company", "Latest adjusted close", "Total return (%)", "Start date", "End date"]]
st.dataframe(
    table.style.format({"Latest adjusted close": "${:,.2f}", "Total return (%)": "{:+.2f}%"}),
    use_container_width=True, hide_index=True
)

csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered data (CSV)", data=csv,
    file_name="stock_comparison_filtered.csv", mime="text/csv"
)
st.caption("Visualizations: indexed performance, adjusted closing price, daily returns, return distribution, rolling volatility, total return, and trading volume.")
