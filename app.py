import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from analysis import (
    fetch_stock_data,
    get_price_targets,
    generate_scenarios,
    get_market_status,
    fetch_stock_news,
    analyze_news_sentiment,
)

# 1. Page Configuration (Must be first)
st.set_page_config(
    page_title="Stock Analyzer & Bull/Bear Scenarios",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .bull-card {
        background: linear-gradient(135deg, rgba(22, 163, 74, 0.08) 0%, rgba(34, 197, 94, 0.02) 100%);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 10px;
        padding: 20px;
    }
    .bear-card {
        background: linear-gradient(135deg, rgba(220, 38, 38, 0.08) 0%, rgba(239, 68, 68, 0.02) 100%);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 10px;
        padding: 20px;
    }
    .news-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
        transition: transform 0.1s ease;
    }
    .news-card:hover {
        border-color: #3b82f6;
    }
    .market-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        background-color: #f1f5f9;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 2. Sidebar Controls
st.sidebar.title("🔍 Stock Selection")

quick_tickers = ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN", "GOOGL"]
selected_quick = st.sidebar.selectbox("Quick Picks", ["Choose one..."] + quick_tickers)
default_ticker = selected_quick if selected_quick != "Choose one..." else "NVDA"

ticker_input = st.sidebar.text_input("Or enter custom symbol:", value=default_ticker).strip().upper()

timeframe = st.sidebar.selectbox(
    "Historical Period:",
    options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3,
)

chart_type = st.sidebar.radio("Chart Type:", ["Candlestick", "Line"], index=0)
show_sma = st.sidebar.checkbox("Show 20 & 50-Day Moving Averages", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("⚡ Live Settings")
auto_refresh = st.sidebar.toggle("Auto-Refresh Live Prices (15s)", value=False)

st.sidebar.markdown("---")
st.sidebar.subheader("🤖 AI Copilot (Gemini)")
# Read from Streamlit secrets if present, or allow manual input
secrets_api_key = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""
gemini_key_input = st.sidebar.text_input(
    "Gemini API Key (optional):",
    value=secrets_api_key,
    type="password",
    help="Get a free key from aistudio.google.com to power AI news sentiment analysis.",
)
gemini_key = gemini_key_input.strip() or secrets_api_key

# 3. Market Open/Closed Status
market_info = get_market_status()

# 4. Data Fetching
@st.cache_data(ttl=15 if auto_refresh else 300, show_spinner=False)
def load_data(symbol: str, period: str):
    return fetch_stock_data(symbol, period)

# Handle Auto-refresh container
def render_dashboard():
    with st.spinner(f"Fetching market data for {ticker_input}..."):
        try:
            df, info, err = load_data(ticker_input, timeframe)
        except Exception as e:
            df, info, err = None, None, f"Error: {e}"

    if err or df is None or info is None or df.empty:
        st.error(f"⚠️ {err or 'Unable to load data. Please check ticker symbol.'}")
        st.info("Tip: If Yahoo Finance is temporarily busy, try selecting another stock or refresh.")
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
    currency = info.get("currency", "USD")
    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")

    # Top Header
    st.markdown(f'<div class="market-badge">{market_info["badge"]} &nbsp;•&nbsp; {market_info["details"]}</div>', unsafe_allow_html=True)
    
    col_head1, col_head2 = st.columns([3, 1])
    with col_head1:
        st.title(f"{company_name} ({ticker_input})")
        st.caption(f"Sector: **{sector}** | Industry: **{industry}** | Currency: **{currency}**")

    with col_head2:
        st.metric(
            label="Current Price",
            value=f"${current_price:,.2f}",
            delta=f"{day_change:+,.2f} ({day_change_pct:+.2f}%)",
        )

    # Key Statistics Bar
    pe_ratio = info.get("trailingPE") or info.get("forwardPE")
    market_cap = info.get("marketCap")
    mcap_str = f"${market_cap / 1e12:.2f}T" if market_cap and market_cap >= 1e12 else (f"${market_cap / 1e9:.2f}B" if market_cap else "N/A")
    week_52_high = info.get("fiftyTwoWeekHigh")
    week_52_low = info.get("fiftyTwoWeekLow")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Market Cap", mcap_str)
    kpi2.metric("P/E Ratio", f"{pe_ratio:.1f}x" if pe_ratio else "N/A")
    kpi3.metric("52-Week High", f"${week_52_high:,.2f}" if week_52_high else "N/A")
    kpi4.metric("52-Week Low", f"${week_52_low:,.2f}" if week_52_low else "N/A")

    st.markdown("---")

    # Main Navigation Tabs
    tab_analysis, tab_ai_copilot = st.tabs(["📊 Stock Analysis & Scenarios", "🤖 AI News Sentiment Copilot"])

    with tab_analysis:
        # Analyst Targets
        try:
            targets = get_price_targets(info, current_price)
        except Exception:
            targets = {"high": None, "low": None, "mean": None, "recommendation": "N/A", "opinions_count": 0, "upside_mean_pct": None, "upside_high_pct": None, "downside_low_pct": None}

        st.subheader("🎯 Wall Street Analyst Price Targets")
        t_col1, t_col2, t_col3, t_col4 = st.columns(4)
        t_col1.metric("Low Target", f"${targets['low']:,.2f}" if targets["low"] else "N/A", delta=f"{targets['downside_low_pct']:+.1f}%" if targets["downside_low_pct"] else None, delta_color="inverse")
        t_col2.metric("Consensus Mean", f"${targets['mean']:,.2f}" if targets["mean"] else "N/A", delta=f"{targets['upside_mean_pct']:+.1f}%" if targets["upside_mean_pct"] else None)
        t_col3.metric("High Target", f"${targets['high']:,.2f}" if targets["high"] else "N/A", delta=f"{targets['upside_high_pct']:+.1f}%" if targets["upside_high_pct"] else None)
        t_col4.metric("Consensus Rating", targets["recommendation"], f"Based on {targets['opinions_count']} analysts", delta_color="off")

        # Range Chart
        if targets["low"] and targets["high"] and targets["mean"]:
            fig_target = go.Figure()
            fig_target.add_trace(go.Bar(
                y=["Price Range"],
                x=[targets["high"] - targets["low"]],
                base=[targets["low"]],
                orientation="h",
                marker=dict(color="rgba(100, 116, 139, 0.2)"),
                name="Range",
                hoverinfo="none",
            ))
            fig_target.add_trace(go.Scatter(x=[targets["low"]], y=["Price Range"], mode="markers+text", name="Low", text=[f"Low: ${targets['low']:.0f}"], textposition="bottom center", marker=dict(color="#EF4444", size=14, symbol="diamond")))
            fig_target.add_trace(go.Scatter(x=[current_price], y=["Price Range"], mode="markers+text", name="Current", text=[f"Current: ${current_price:.2f}"], textposition="top center", marker=dict(color="#3B82F6", size=16, symbol="circle")))
            fig_target.add_trace(go.Scatter(x=[targets["mean"]], y=["Price Range"], mode="markers+text", name="Mean", text=[f"Mean: ${targets['mean']:.0f}"], textposition="bottom center", marker=dict(color="#F59E0B", size=14, symbol="triangle-up")))
            fig_target.add_trace(go.Scatter(x=[targets["high"]], y=["Price Range"], mode="markers+text", name="High", text=[f"High: ${targets['high']:.0f}"], textposition="bottom center", marker=dict(color="#10B981", size=14, symbol="diamond")))
            fig_target.update_layout(height=140, margin=dict(l=20, r=20, t=20, b=20), xaxis=dict(showgrid=True, title="Price ($)"), yaxis=dict(showticklabels=False), showlegend=False)
            st.plotly_chart(fig_target, use_container_width=True)

        st.write("")

        # Bull vs Bear Scenarios
        st.subheader("⚖️ Bull & Bear Scenario Analysis")
        try:
            scenarios = generate_scenarios(info, df, current_price, targets)
            col_bull, col_bear = st.columns(2)
            with col_bull:
                bull = scenarios["bull"]
                st.markdown(f"""
                <div class="bull-card">
                    <h3 style="color: #16A34A; margin-top: 0;">🟢 BULL CASE (Optimistic)</h3>
                    <p style="font-size: 1.25rem; font-weight: bold; margin-bottom: 5px;">
                        Target Price: ${bull['target']:,.2f} <span style="color: #16A34A; font-size: 1rem;">(+{bull['upside_pct']:.1f}% Upside)</span>
                    </p>
                    <p style="color: #555;">Key Catalysts & Tailwinds:</p>
                    <ul style="line-height: 1.8;">{''.join([f"<li>{item}</li>" for item in bull['catalysts']])}</ul>
                </div>
                """, unsafe_allow_html=True)

            with col_bear:
                bear = scenarios["bear"]
                st.markdown(f"""
                <div class="bear-card">
                    <h3 style="color: #DC2626; margin-top: 0;">🔴 BEAR CASE (Pessimistic)</h3>
                    <p style="font-size: 1.25rem; font-weight: bold; margin-bottom: 5px;">
                        Target Price: ${bear['target']:,.2f} <span style="color: #DC2626; font-size: 1rem;">({bear['downside_pct']:.1f}% Downside)</span>
                    </p>
                    <p style="color: #555;">Key Risks & Headwinds:</p>
                    <ul style="line-height: 1.8;">{''.join([f"<li>{item}</li>" for item in bear['risks']])}</ul>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Scenario error: {e}")

        st.write("")
        st.markdown("---")

        # Interactive Chart
        st.subheader("📊 Price Action & Technical Momentum")
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.75, 0.25])
        if chart_type == "Candlestick":
            fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="Price"), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Close", line=dict(color="#3B82F6", width=2)), row=1, col=1)

        if show_sma:
            if "SMA_20" in df:
                fig.add_trace(go.Scatter(x=df.index, y=df["SMA_20"], mode="lines", name="20 SMA", line=dict(color="#F59E0B", width=1.5)), row=1, col=1)
            if "SMA_50" in df:
                fig.add_trace(go.Scatter(x=df.index, y=df["SMA_50"], mode="lines", name="50 SMA", line=dict(color="#8B5CF6", width=1.5)), row=1, col=1)

        colors = ["#EF4444" if r["Open"] > r["Close"] else "#10B981" for _, r in df.iterrows()]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=colors, name="Volume", opacity=0.6), row=2, col=1)
        fig.update_layout(height=550, xaxis_rangeslider_visible=False, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        st.plotly_chart(fig, use_container_width=True)

        # CSV Download
        with st.expander("📁 View & Download Historical Price Data"):
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)
            csv = df.to_csv().encode("utf-8")
            st.download_button(label=f"📥 Download {ticker_input} CSV Data", data=csv, file_name=f"{ticker_input}_historical_data.csv", mime="text/csv")

    with tab_ai_copilot:
        st.subheader(f"🤖 AI Market Sentiment & News Analysis for {company_name}")
        
        news_items = fetch_stock_news(ticker_input)
        if not news_items:
            st.info(f"No recent news articles found for {ticker_input}.")
        else:
            with st.spinner("Analyzing news sentiment..."):
                sentiment = analyze_news_sentiment(gemini_key, ticker_input, news_items, current_price, company_name)

            # Sentiment Meter Gauge
            col_s1, col_s2 = st.columns([1, 2])
            with col_s1:
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=sentiment["score"],
                    title={'text': f"Sentiment Score: {sentiment['label']}"},
                    gauge={
                        'axis': {'range': [-10, 10], 'tickwidth': 1},
                        'bar': {'color': sentiment["color"]},
                        'steps': [
                            {'range': [-10, -3], 'color': "rgba(239, 68, 68, 0.2)"},
                            {'range': [-3, 3], 'color': "rgba(245, 158, 11, 0.2)"},
                            {'range': [3, 10], 'color': "rgba(34, 197, 94, 0.2)"},
                        ],
                    }
                ))
                fig_gauge.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_gauge, use_container_width=True)

            with col_s2:
                st.markdown(f"#### 📝 Executive Market Summary")
                st.write(sentiment["summary"])
                st.caption(f"Engine: **{sentiment.get('source', 'AI')}**")
                
                st.markdown("##### 📌 Key Takeaways")
                for point in sentiment.get("takeaways", []):
                    st.markdown(f"• {point}")

            st.markdown("---")
            st.subheader("📰 Recent Headlines & Sources")
            for item in news_items:
                st.markdown(f"""
                <div class="news-card">
                    <a href="{item['link']}" target="_blank" style="text-decoration: none; color: #1e293b; font-size: 1.05rem; font-weight: 600;">
                        🔗 {item['title']}
                    </a>
                    <div style="font-size: 0.82rem; color: #64748b; margin-top: 6px;">
                        Source: <b>{item['publisher']}</b> &nbsp;•&nbsp; Published: {item['time']}
                    </div>
                </div>
                """, unsafe_allow_html=True)


# Execute with optional auto-refresh fragment
if auto_refresh and hasattr(st, "fragment"):
    @st.fragment(run_every="15s")
    def live_container():
        render_dashboard()
    live_container()
else:
    render_dashboard()
