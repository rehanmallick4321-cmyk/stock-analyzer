import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from analysis import (
    fetch_stock_data,
    get_price_targets,
    generate_scenarios,
    get_market_status,
    get_pre_post_market,
    fetch_stock_news,
    analyze_news_sentiment,
    format_ticker_metadata,
)

# 1. Page Configuration with Enhanced Branding Symbol
st.set_page_config(
    page_title="APEX // Global Market Terminal",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Sidebar Controls & Branding
st.sidebar.markdown("""
<div style="margin-bottom: 15px;">
    <h2 style="margin: 0; font-size: 1.6rem; font-weight: 800; letter-spacing: -0.02em;">
        💎 APEX TERMINAL
    </h2>
    <div style="font-size: 0.8rem; opacity: 0.7; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;">
        Global Equity Intelligence & AI Analytics
    </div>
</div>
""", unsafe_allow_html=True)

# Market / Region Selector
market_region = st.sidebar.radio(
    "Select Market Exchange:",
    ["🇮🇳 Indian Markets (NSE)", "🇺🇸 US Markets (NYSE/NASDAQ)"],
    index=0,
)

# Standardized Ticker Catalog with Clear Company Names
INDIAN_STOCKS = {
    "RELIANCE": {"symbol": "RELIANCE.NS", "label": "RELIANCE • Reliance Industries"},
    "TCS": {"symbol": "TCS.NS", "label": "TCS • Tata Consultancy Services"},
    "HDFCBANK": {"symbol": "HDFCBANK.NS", "label": "HDFCBANK • HDFC Bank"},
    "INFY": {"symbol": "INFY.NS", "label": "INFY • Infosys Limited"},
    "TATAMOTORS": {"symbol": "TATAMOTORS.NS", "label": "TATAMOTORS • Tata Motors"},
    "ITC": {"symbol": "ITC.NS", "label": "ITC • ITC Limited"},
    "ICICIBANK": {"symbol": "ICICIBANK.NS", "label": "ICICIBANK • ICICI Bank"},
    "SBIN": {"symbol": "SBIN.NS", "label": "SBIN • State Bank of India"},
    "BHARTIARTL": {"symbol": "BHARTIARTL.NS", "label": "BHARTIARTL • Bharti Airtel"},
    "ZOMATO": {"symbol": "ZOMATO.NS", "label": "ZOMATO • Zomato Limited"},
}

US_STOCKS = {
    "NVDA": {"symbol": "NVDA", "label": "NVDA • NVIDIA Corporation"},
    "AAPL": {"symbol": "AAPL", "label": "AAPL • Apple Inc"},
    "MSFT": {"symbol": "MSFT", "label": "MSFT • Microsoft Corporation"},
    "TSLA": {"symbol": "TSLA", "label": "TSLA • Tesla Inc"},
    "AMZN": {"symbol": "AMZN", "label": "AMZN • Amazon.com Inc"},
    "GOOGL": {"symbol": "GOOGL", "label": "GOOGL • Alphabet Inc"},
}

if market_region == "🇮🇳 Indian Markets (NSE)":
    catalog = INDIAN_STOCKS
    default_key = "RELIANCE"
else:
    catalog = US_STOCKS
    default_key = "NVDA"

options = ["Choose from Popular..."] + [item["label"] for item in catalog.values()]
selected_option = st.sidebar.selectbox("Standard Watchlist", options)

if selected_option != "Choose from Popular...":
    # Match symbol from selected option
    matched_sym = [item["symbol"] for item in catalog.values() if item["label"] == selected_option][0]
    default_input_val = matched_sym.replace(".NS", "").replace(".BO", "")
else:
    default_input_val = default_key

raw_ticker = st.sidebar.text_input("Or Enter Custom Ticker:", value=default_input_val).strip().upper()

# Standardize ticker formatting behind the scenes
if market_region == "🇮🇳 Indian Markets (NSE)":
    if not raw_ticker.endswith(".NS") and not raw_ticker.endswith(".BO"):
        ticker_input = f"{raw_ticker}.NS"
    else:
        ticker_input = raw_ticker
else:
    ticker_input = raw_ticker

timeframe = st.sidebar.selectbox(
    "Chart Period:",
    options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3,
)

chart_type = st.sidebar.radio("Display Style:", ["Candlestick", "Line"], index=0)
show_sma = st.sidebar.checkbox("Show 20 & 50-Day Moving Averages", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("🔴 Live Ticking")
auto_refresh = st.sidebar.toggle("Auto-Refresh Market (15s)", value=False)

st.sidebar.markdown("---")
st.sidebar.subheader("🤖 AI News Analyst")
secrets_api_key = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""
gemini_key_input = st.sidebar.text_input(
    "Google Gemini API Key (optional):",
    value=secrets_api_key,
    type="password",
    help="Get a free key from aistudio.google.com to power AI sentiment reasoning.",
)
gemini_key = gemini_key_input.strip() or secrets_api_key

# 3. Market Session Status
market_info = get_market_status(ticker_input)

# 4. Data Loading
@st.cache_data(ttl=15 if auto_refresh else 300, show_spinner=False)
def load_data(symbol: str, period: str):
    return fetch_stock_data(symbol, period)

def render_terminal():
    with st.spinner(f"Connecting to market feed for {ticker_input}..."):
        try:
            df, info, err = load_data(ticker_input, timeframe)
        except Exception as e:
            df, info, err = None, None, f"Error: {e}"

    if err or df is None or info is None or df.empty:
        st.error(f"⚠️ {err or 'Unable to load data. Please check ticker symbol.'}")
        if market_region == "🇮🇳 Indian Markets (NSE)":
            st.info("Tip for Indian stocks: Enter standard symbols like RELIANCE, TCS, INFY, HDFCBANK, or TATAMOTORS.")
        st.stop()

    close_series = df["Close"].dropna()
    if len(close_series) == 0:
        st.error("No valid price data.")
        st.stop()

    current_price = float(close_series.iloc[-1])
    prev_close = float(close_series.iloc[-2]) if len(close_series) > 1 else current_price
    day_change = current_price - prev_close
    day_change_pct = (day_change / prev_close * 100) if prev_close else 0.0

    company_name = info.get("longName", ticker_input)
    currency = (info.get("currency") or ("INR" if ticker_input.endswith(".NS") or ticker_input.endswith(".BO") else "USD")).upper()
    curr_sym = "₹" if currency == "INR" else ("€" if currency == "EUR" else ("£" if currency == "GBP" else "$"))
    
    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")

    # Standardized Ticker Metadata (e.g. 'NSE: RELIANCE' or 'NASDAQ: NVDA')
    meta = format_ticker_metadata(ticker_input, info)

    # Pre-Market and Post-Market Data
    ext_data = get_pre_post_market(info, current_price)
    active_session = market_info.get("session", "REGULAR")

    # --- Header Top Bar ---
    status_icon = "🟢" if active_session == "REGULAR" else ("🟡" if active_session == "PRE" else ("🌙" if active_session == "POST" else "🔴"))
    st.info(f"{status_icon} **{market_info['badge']}** &nbsp;•&nbsp; {market_info['details']}")

    # Standardized Company & Ticker Header
    col_title, col_meta = st.columns([3, 1])
    with col_title:
        st.title(f"🏛️ {company_name}")
        st.markdown(
            f"**`{meta['flag']} {meta['standard_display']}`** &nbsp;|&nbsp; "
            f"Exchange: **{meta['exchange_name']}** &nbsp;|&nbsp; "
            f"Currency: **{currency} ({curr_sym})** &nbsp;|&nbsp; "
            f"Sector: **{sector}**"
        )
    with col_meta:
        st.write("")
        st.caption("💎 **APEX EQUITY FEED**")
        st.caption(f"Asset Class: **{meta['market_tag']}**")

    st.write("")

    # --- Live Multi-Session Price Cards (Native Streamlit Containers) ---
    col_reg, col_pre, col_post = st.columns(3)

    # 1. Regular Market Price Card
    with col_reg:
        with st.container(border=True):
            reg_label = f"🏢 REGULAR SESSION ({meta['standard_display']})" if active_session == "REGULAR" else f"🏢 Regular Session ({meta['standard_display']})"
            st.metric(
                label=reg_label,
                value=f"{curr_sym}{current_price:,.2f}",
                delta=f"{day_change:+,.2f} ({day_change_pct:+.2f}%)",
            )

    # 2. Pre-Market Price Card
    with col_pre:
        with st.container(border=True):
            pre_val = ext_data["pre_price"]
            if pre_val:
                pre_change = ext_data["pre_change"] or 0.0
                pre_pct = ext_data["pre_pct"] or 0.0
                pre_label = "🌅 PRE-MARKET (LIVE NOW)" if active_session == "PRE" else "🌅 Pre-Market Price"
                st.metric(
                    label=pre_label,
                    value=f"{curr_sym}{pre_val:,.2f}",
                    delta=f"{pre_change:+,.2f} ({pre_pct:+.2f}%) vs Close",
                )
            else:
                st.metric(
                    label="🌅 Pre-Market / Call Auction",
                    value="Closed / N/A",
                    delta="Pre-open session",
                    delta_color="off",
                )

    # 3. Post-Market / After-Hours Price Card
    with col_post:
        with st.container(border=True):
            post_val = ext_data["post_price"]
            if post_val:
                post_change = ext_data["post_change"] or 0.0
                post_pct = ext_data["post_pct"] or 0.0
                post_label = "🌙 POST-MARKET (LIVE NOW)" if active_session == "POST" else "🌙 Post-Market Price"
                st.metric(
                    label=post_label,
                    value=f"{curr_sym}{post_val:,.2f}",
                    delta=f"{post_change:+,.2f} ({post_pct:+.2f}%) vs Close",
                )
            else:
                st.metric(
                    label="🌙 Post-Market / After-Hours",
                    value="Closed / N/A",
                    delta="Closing session",
                    delta_color="off",
                )

    st.write("")

    # --- KPI Tiles Bar with Indian & US formatting ---
    pe_ratio = info.get("trailingPE") or info.get("forwardPE")
    market_cap = info.get("marketCap")
    
    if market_cap:
        if currency == "INR":
            if market_cap >= 1e12:
                mcap_str = f"₹{market_cap / 1e12:.2f} Lakh Cr"
            else:
                mcap_str = f"₹{market_cap / 1e7:,.0f} Cr"
        else:
            if market_cap >= 1e12:
                mcap_str = f"${market_cap / 1e12:.2f}T"
            else:
                mcap_str = f"${market_cap / 1e9:.2f}B"
    else:
        mcap_str = "N/A"

    pe_str = f"{pe_ratio:.1f}x" if pe_ratio else "N/A"
    week_52_high = info.get("fiftyTwoWeekHigh")
    week_52_low = info.get("fiftyTwoWeekLow")
    high_str = f"{curr_sym}{week_52_high:,.2f}" if week_52_high else "N/A"
    low_str = f"{curr_sym}{week_52_low:,.2f}" if week_52_low else "N/A"

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Market Capitalization", mcap_str)
    k2.metric("P/E Valuation Ratio", pe_str)
    k3.metric("52-Week Peak High", high_str)
    k4.metric("52-Week Floor Low", low_str)

    st.write("")

    # --- Main Navigation Tabs ---
    tab_analysis, tab_ai_copilot = st.tabs(["📈 Market Analytics & Scenarios", "🤖 AI News Sentiment Copilot"])

    with tab_analysis:
        targets = get_price_targets(info, current_price)
        st.subheader("🎯 Analyst Consensus & Price Targets")

        tc1, tc2, tc3, tc4 = st.columns(4)
        tc1.metric("Analyst Low", f"{curr_sym}{targets['low']:,.2f}" if targets["low"] else "N/A", delta=f"{targets['downside_low_pct']:+.1f}%" if targets["downside_low_pct"] else None, delta_color="inverse")
        tc2.metric("Consensus Mean", f"{curr_sym}{targets['mean']:,.2f}" if targets["mean"] else "N/A", delta=f"{targets['upside_mean_pct']:+.1f}%" if targets["upside_mean_pct"] else None)
        tc3.metric("Analyst High", f"{curr_sym}{targets['high']:,.2f}" if targets["high"] else "N/A", delta=f"{targets['upside_high_pct']:+.1f}%" if targets["upside_high_pct"] else None)
        tc4.metric("Consensus Rating", targets["recommendation"], f"{targets['opinions_count']} analysts reporting", delta_color="off")

        # Visual Range Spread
        if targets["low"] and targets["high"] and targets["mean"]:
            fig_target = go.Figure()
            fig_target.add_trace(go.Bar(
                y=["Price Range"],
                x=[targets["high"] - targets["low"]],
                base=[targets["low"]],
                orientation="h",
                marker=dict(color="rgba(148, 163, 184, 0.3)"),
                name="Spread",
                hoverinfo="none",
            ))
            fig_target.add_trace(go.Scatter(x=[targets["low"]], y=["Price Range"], mode="markers+text", name="Low", text=[f"Low {curr_sym}{targets['low']:.0f}"], textposition="bottom center", marker=dict(color="#EF4444", size=14, symbol="diamond")))
            fig_target.add_trace(go.Scatter(x=[current_price], y=["Price Range"], mode="markers+text", name="Current", text=[f"Current {curr_sym}{current_price:,.2f}"], textposition="top center", marker=dict(color="#3B82F6", size=16, symbol="circle", line=dict(color="#ffffff", width=2))))
            fig_target.add_trace(go.Scatter(x=[targets["mean"]], y=["Price Range"], mode="markers+text", name="Mean", text=[f"Mean {curr_sym}{targets['mean']:.0f}"], textposition="bottom center", marker=dict(color="#F59E0B", size=14, symbol="triangle-up")))
            fig_target.add_trace(go.Scatter(x=[targets["high"]], y=["Price Range"], mode="markers+text", name="High", text=[f"High {curr_sym}{targets['high']:.0f}"], textposition="bottom center", marker=dict(color="#10B981", size=14, symbol="diamond")))
            fig_target.update_layout(
                height=140,
                margin=dict(l=20, r=20, t=25, b=25),
                xaxis=dict(showgrid=True, title=f"Price ({currency})", zeroline=False),
                yaxis=dict(showticklabels=False),
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="gray"),
            )
            st.plotly_chart(fig_target, use_container_width=True)

        st.write("")

        # Bull vs Bear Scenarios
        st.subheader("⚖️ Bull & Bear Scenario Engine")
        scenarios = generate_scenarios(info, df, current_price, targets, curr_sym)
        cbull, cbear = st.columns(2)
        with cbull:
            bull = scenarios["bull"]
            with st.container(border=True):
                st.subheader("🟢 BULL CASE (Optimistic)")
                st.metric("Target Price", f"{curr_sym}{bull['target']:,.2f}", delta=f"+{bull['upside_pct']:.1f}% Upside")
                st.write("**Growth Catalysts & Tailwinds:**")
                for item in bull["catalysts"]:
                    st.markdown(f"• {item}")

        with cbear:
            bear = scenarios["bear"]
            with st.container(border=True):
                st.subheader("🔴 BEAR CASE (Pessimistic)")
                st.metric("Target Price", f"{curr_sym}{bear['target']:,.2f}", delta=f"{bear['downside_pct']:.1f}% Downside", delta_color="inverse")
                st.write("**Risk Factors & Headwinds:**")
                for item in bear["risks"]:
                    st.markdown(f"• {item}")

        st.write("")
        st.markdown("---")

        # Technical Charting
        st.subheader("📊 Interactive Technical Action")
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.75, 0.25])
        if chart_type == "Candlestick":
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                increasing_line_color="#10B981",
                decreasing_line_color="#EF4444",
                name="Candles",
            ), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df["Close"],
                mode="lines",
                name="Close",
                line=dict(color="#3B82F6", width=2.5),
            ), row=1, col=1)

        if show_sma:
            if "SMA_20" in df:
                fig.add_trace(go.Scatter(x=df.index, y=df["SMA_20"], mode="lines", name="20 SMA", line=dict(color="#F59E0B", width=1.5)), row=1, col=1)
            if "SMA_50" in df:
                fig.add_trace(go.Scatter(x=df.index, y=df["SMA_50"], mode="lines", name="50 SMA", line=dict(color="#8B5CF6", width=1.5)), row=1, col=1)

        vol_colors = ["#EF4444" if r["Open"] > r["Close"] else "#10B981" for _, r in df.iterrows()]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=vol_colors, name="Volume", opacity=0.6), row=2, col=1)

        fig.update_layout(
            height=560,
            xaxis_rangeslider_visible=False,
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="gray"),
            xaxis=dict(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)"),
            yaxis=dict(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)", title=f"Price ({curr_sym})"),
            yaxis2=dict(showgrid=False, title="Volume"),
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📁 View & Download Historical Price Data"):
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)
            csv = df.to_csv().encode("utf-8")
            st.download_button(label=f"📥 Download {meta['base_symbol']} CSV Data", data=csv, file_name=f"{meta['base_symbol']}_historical_data.csv", mime="text/csv")

    with tab_ai_copilot:
        st.subheader(f"🤖 AI Market Sentiment & Intelligence for {company_name}")
        news_items = fetch_stock_news(ticker_input)

        if not news_items:
            st.info(f"No recent news articles found for {meta['standard_display']}.")
        else:
            with st.spinner("Analyzing market sentiment from news releases..."):
                sentiment = analyze_news_sentiment(gemini_key, ticker_input, news_items, current_price, company_name, curr_sym)

            sg1, sg2 = st.columns([1, 2])
            with sg1:
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=sentiment["score"],
                    title={'text': f"<b>Sentiment: {sentiment['label']}</b>", 'font': {'size': 16, 'color': "gray"}},
                    gauge={
                        'axis': {'range': [-10, 10], 'tickwidth': 1, 'tickcolor': "#94a3b8"},
                        'bar': {'color': sentiment["color"], 'thickness': 0.3},
                        'steps': [
                            {'range': [-10, -3], 'color': "rgba(239, 68, 68, 0.2)"},
                            {'range': [-3, 3], 'color': "rgba(245, 158, 11, 0.2)"},
                            {'range': [3, 10], 'color': "rgba(16, 185, 129, 0.2)"},
                        ],
                    }
                ))
                fig_gauge.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="rgba(0,0,0,0)", font=dict(color="gray"))
                st.plotly_chart(fig_gauge, use_container_width=True)

            with sg2:
                st.markdown(f"#### 📝 Executive Market Summary")
                st.write(sentiment["summary"])
                st.caption(f"Engine: **{sentiment.get('source', 'AI')}**")

                st.markdown("##### 📌 Key Catalyst Takeaways")
                for point in sentiment.get("takeaways", []):
                    st.markdown(f"• {point}")

            st.markdown("---")
            st.subheader(f"📰 Latest News Articles & Press Releases ({len(news_items)})")
            for item in news_items:
                with st.container(border=True):
                    st.markdown(f"**[{item['title']}]({item['link']})**")
                    st.caption(f"Source: **{item['publisher']}** &nbsp;•&nbsp; Published: {item['time']}")


# Auto-refresh execution
if auto_refresh and hasattr(st, "fragment"):
    @st.fragment(run_every="15s")
    def live_container():
        render_terminal()
    live_container()
else:
    render_terminal()
