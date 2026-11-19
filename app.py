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
)

# 1. Page Configuration (Must be first)
st.set_page_config(
    page_title="Stock Analyzer & Live Market Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Modern Responsive Dark/Light Compatible Styling using Streamlit Theme Variables
st.markdown("""
<style>
    /* Card containers using Streamlit theme variables for 100% Dark/Light compatibility */
    .price-badge-card {
        background-color: var(--secondary-background-color, #1e293b);
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .price-badge-card:hover {
        transform: translateY(-2px);
    }
    .price-badge-card.active-session {
        border: 2px solid #3b82f6 !important;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.25);
    }
    .price-title {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-color, #94a3b8);
        opacity: 0.85;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .price-value {
        font-size: 1.7rem;
        font-weight: 800;
        color: var(--text-color, #f8fafc);
        line-height: 1.2;
    }
    .price-delta {
        font-size: 0.9rem;
        font-weight: 600;
        margin-top: 4px;
    }
    .delta-green { color: #10b981 !important; font-weight: 700; }
    .delta-red { color: #ef4444 !important; font-weight: 700; }
    .delta-neutral { color: var(--text-color, #94a3b8) !important; opacity: 0.7; }

    /* Bull & Bear Adaptive Cards */
    .bull-card-modern {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(5, 150, 105, 0.04) 100%);
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 14px;
        padding: 22px 24px;
        color: var(--text-color, #f8fafc);
    }
    .bear-card-modern {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(185, 28, 28, 0.04) 100%);
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-radius: 14px;
        padding: 22px 24px;
        color: var(--text-color, #f8fafc);
    }

    /* KPI metric tiles */
    .kpi-tile {
        background-color: var(--secondary-background-color, #1e293b);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    }
    .kpi-label {
        font-size: 0.8rem;
        color: var(--text-color, #94a3b8);
        opacity: 0.8;
        font-weight: 600;
        text-transform: uppercase;
    }
    .kpi-value {
        font-size: 1.4rem;
        font-weight: 800;
        color: var(--text-color, #f8fafc);
        margin-top: 4px;
    }

    /* Live Session Status Pill */
    .session-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 16px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 700;
        background-color: var(--secondary-background-color, #1e293b);
        border: 1px solid rgba(148, 163, 184, 0.25);
        color: var(--text-color, #f8fafc);
        margin-bottom: 12px;
    }

    /* News card */
    .news-card-styled {
        background-color: var(--secondary-background-color, #1e293b);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 14px;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .news-card-styled:hover {
        transform: translateY(-2px);
        border-color: #3b82f6;
    }
    .news-title-link {
        text-decoration: none;
        color: var(--text-color, #f8fafc) !important;
        font-size: 1.05rem;
        font-weight: 700;
        display: block;
        margin-bottom: 6px;
    }
    .news-title-link:hover {
        color: #3b82f6 !important;
    }
</style>
""", unsafe_allow_html=True)

# 2. Sidebar Controls
st.sidebar.title("⚡ Stock Terminal")

quick_tickers = ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN", "GOOGL"]
selected_quick = st.sidebar.selectbox("Popular Stocks", ["Choose one..."] + quick_tickers)
default_ticker = selected_quick if selected_quick != "Choose one..." else "NVDA"

ticker_input = st.sidebar.text_input("Ticker Symbol:", value=default_ticker).strip().upper()

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
market_info = get_market_status()

# 4. Data Loading
@st.cache_data(ttl=15 if auto_refresh else 300, show_spinner=False)
def load_data(symbol: str, period: str):
    return fetch_stock_data(symbol, period)

def render_terminal():
    with st.spinner(f"Loading live quote and charts for {ticker_input}..."):
        try:
            df, info, err = load_data(ticker_input, timeframe)
        except Exception as e:
            df, info, err = None, None, f"Error: {e}"

    if err or df is None or info is None or df.empty:
        st.error(f"⚠️ {err or 'Unable to load data. Please check ticker symbol.'}")
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

    # Pre-Market and Post-Market Data
    ext_data = get_pre_post_market(info, current_price)
    active_session = market_info.get("session", "REGULAR")

    # Header Top Bar
    st.markdown(f'''
    <div class="session-pill">
        <span style="color: {market_info["color"]}; font-size: 1.1rem;">●</span>
        <span><b>{market_info["badge"]}</b> &nbsp;•&nbsp; {market_info["details"]}</span>
    </div>
    ''', unsafe_allow_html=True)

    st.title(f"{company_name} ({ticker_input})")
    st.caption(f"Sector: **{sector}** &nbsp;•&nbsp; Industry: **{industry}** &nbsp;•&nbsp; Currency: **{currency}**")

    # --- Live Multi-Session Price Cards (Regular, Pre-Market, After-Hours) ---
    col_reg, col_pre, col_post = st.columns(3)

    # 1. Regular Market Price Card
    reg_active = "active-session" if active_session == "REGULAR" else ""
    reg_class = "delta-green" if day_change >= 0 else "delta-red"
    reg_sign = "+" if day_change >= 0 else ""
    with col_reg:
        st.markdown(f"""
        <div class="price-badge-card {reg_active}">
            <div class="price-title">
                <span>🏢 Regular Market</span>
                {"<span style='color:#3b82f6; font-size:0.7rem;'>● ACTIVE</span>" if active_session == "REGULAR" else ""}
            </div>
            <div class="price-value">${current_price:,.2f}</div>
            <div class="price-delta {reg_class}">{reg_sign}{day_change:,.2f} ({reg_sign}{day_change_pct:.2f}%)</div>
        </div>
        """, unsafe_allow_html=True)

    # 2. Pre-Market Price Card
    pre_active = "active-session" if active_session == "PRE" else ""
    pre_val = ext_data["pre_price"]
    with col_pre:
        if pre_val:
            pre_change = ext_data["pre_change"] or 0.0
            pre_pct = ext_data["pre_pct"] or 0.0
            pre_class = "delta-green" if pre_pct >= 0 else "delta-red"
            pre_sign = "+" if pre_pct >= 0 else ""
            st.markdown(f"""
            <div class="price-badge-card {pre_active}">
                <div class="price-title">
                    <span>🌅 Pre-Market Price</span>
                    {"<span style='color:#f59e0b; font-size:0.7rem;'>● LIVE</span>" if active_session == "PRE" else ""}
                </div>
                <div class="price-value">${pre_val:,.2f}</div>
                <div class="price-delta {pre_class}">{pre_sign}{pre_change:,.2f} ({pre_sign}{pre_pct:.2f}%) vs Close</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="price-badge-card">
                <div class="price-title">🌅 Pre-Market Price</div>
                <div class="price-value delta-neutral" style="font-size: 1.25rem;">N/A</div>
                <div class="price-delta delta-neutral">Active 4:00 AM – 9:30 AM ET</div>
            </div>
            """, unsafe_allow_html=True)

    # 3. Post-Market / After-Hours Price Card
    post_active = "active-session" if active_session == "POST" else ""
    post_val = ext_data["post_price"]
    with col_post:
        if post_val:
            post_change = ext_data["post_change"] or 0.0
            post_pct = ext_data["post_pct"] or 0.0
            post_class = "delta-green" if post_pct >= 0 else "delta-red"
            post_sign = "+" if post_pct >= 0 else ""
            st.markdown(f"""
            <div class="price-badge-card {post_active}">
                <div class="price-title">
                    <span>🌙 After-Hours Price</span>
                    {"<span style='color:#8b5cf6; font-size:0.7rem;'>● LIVE</span>" if active_session == "POST" else ""}
                </div>
                <div class="price-value">${post_val:,.2f}</div>
                <div class="price-delta {post_class}">{post_sign}{post_change:,.2f} ({post_sign}{post_pct:.2f}%) vs Close</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="price-badge-card">
                <div class="price-title">🌙 After-Hours Price</div>
                <div class="price-value delta-neutral" style="font-size: 1.25rem;">N/A</div>
                <div class="price-delta delta-neutral">Active 4:00 PM – 8:00 PM ET</div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")

    # --- KPI Tiles Bar (Clean values, zero code reflection) ---
    pe_ratio = info.get("trailingPE") or info.get("forwardPE")
    market_cap = info.get("marketCap")
    mcap_str = f"${market_cap / 1e12:.2f}T" if market_cap and market_cap >= 1e12 else (f"${market_cap / 1e9:.2f}B" if market_cap else "N/A")
    pe_str = f"{pe_ratio:.1f}x" if pe_ratio else "N/A"
    week_52_high = info.get("fiftyTwoWeekHigh")
    week_52_low = info.get("fiftyTwoWeekLow")
    high_str = f"${week_52_high:,.2f}" if week_52_high else "N/A"
    low_str = f"${week_52_low:,.2f}" if week_52_low else "N/A"

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="kpi-tile"><div class="kpi-label">Market Capitalization</div><div class="kpi-value">{mcap_str}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-tile"><div class="kpi-label">P/E Valuation Ratio</div><div class="kpi-value">{pe_str}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-tile"><div class="kpi-label">52-Week Peak High</div><div class="kpi-value">{high_str}</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-tile"><div class="kpi-label">52-Week Floor Low</div><div class="kpi-value">{low_str}</div></div>', unsafe_allow_html=True)

    st.write("")

    # --- Main Navigation Tabs ---
    tab_analysis, tab_ai_copilot = st.tabs(["📈 Market Analytics & Scenarios", "🤖 AI News Sentiment Copilot"])

    with tab_analysis:
        # Analyst Targets Section
        targets = get_price_targets(info, current_price)
        st.subheader("🎯 Wall Street Consensus & Price Targets")

        tc1, tc2, tc3, tc4 = st.columns(4)
        tc1.metric("Analyst Low", f"${targets['low']:,.2f}" if targets["low"] else "N/A", delta=f"{targets['downside_low_pct']:+.1f}%" if targets["downside_low_pct"] else None, delta_color="inverse")
        tc2.metric("Consensus Mean", f"${targets['mean']:,.2f}" if targets["mean"] else "N/A", delta=f"{targets['upside_mean_pct']:+.1f}%" if targets["upside_mean_pct"] else None)
        tc3.metric("Analyst High", f"${targets['high']:,.2f}" if targets["high"] else "N/A", delta=f"{targets['upside_high_pct']:+.1f}%" if targets["upside_high_pct"] else None)
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
            fig_target.add_trace(go.Scatter(x=[targets["low"]], y=["Price Range"], mode="markers+text", name="Low", text=[f"Low ${targets['low']:.0f}"], textposition="bottom center", marker=dict(color="#EF4444", size=14, symbol="diamond")))
            fig_target.add_trace(go.Scatter(x=[current_price], y=["Price Range"], mode="markers+text", name="Current", text=[f"Current ${current_price:.2f}"], textposition="top center", marker=dict(color="#3B82F6", size=16, symbol="circle", line=dict(color="#ffffff", width=2))))
            fig_target.add_trace(go.Scatter(x=[targets["mean"]], y=["Price Range"], mode="markers+text", name="Mean", text=[f"Mean ${targets['mean']:.0f}"], textposition="bottom center", marker=dict(color="#F59E0B", size=14, symbol="triangle-up")))
            fig_target.add_trace(go.Scatter(x=[targets["high"]], y=["Price Range"], mode="markers+text", name="High", text=[f"High ${targets['high']:.0f}"], textposition="bottom center", marker=dict(color="#10B981", size=14, symbol="diamond")))
            fig_target.update_layout(
                height=140,
                margin=dict(l=20, r=20, t=25, b=25),
                xaxis=dict(showgrid=True, title="Price ($)", zeroline=False),
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
        scenarios = generate_scenarios(info, df, current_price, targets)
        cbull, cbear = st.columns(2)
        with cbull:
            bull = scenarios["bull"]
            st.markdown(f"""
            <div class="bull-card-modern">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="color: #10b981; margin:0; font-size:1.35rem;">🟢 BULL CASE (Optimistic)</h3>
                    <span style="background: rgba(16,185,129,0.22); color:#10b981; padding:4px 12px; border-radius:9999px; font-weight:700; font-size:0.85rem;">+{bull['upside_pct']:.1f}% UPSIDE</span>
                </div>
                <p style="font-size: 1.5rem; font-weight: 800; margin: 12px 0 6px 0;">
                    Target Price: ${bull['target']:,.2f}
                </p>
                <div style="font-size:0.88rem; font-weight:600; opacity:0.8; margin-bottom:8px;">Growth Catalysts & Tailwinds:</div>
                <ul style="line-height: 1.8; padding-left:20px; margin:0;">
                    {''.join([f"<li>{item}</li>" for item in bull['catalysts']])}
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with cbear:
            bear = scenarios["bear"]
            st.markdown(f"""
            <div class="bear-card-modern">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="color: #ef4444; margin:0; font-size:1.35rem;">🔴 BEAR CASE (Pessimistic)</h3>
                    <span style="background: rgba(239,68,68,0.22); color:#ef4444; padding:4px 12px; border-radius:9999px; font-weight:700; font-size:0.85rem;">{bear['downside_pct']:.1f}% DOWNSIDE</span>
                </div>
                <p style="font-size: 1.5rem; font-weight: 800; margin: 12px 0 6px 0;">
                    Target Price: ${bear['target']:,.2f}
                </p>
                <div style="font-size:0.88rem; font-weight:600; opacity:0.8; margin-bottom:8px;">Risk Factors & Headwinds:</div>
                <ul style="line-height: 1.8; padding-left:20px; margin:0;">
                    {''.join([f"<li>{item}</li>" for item in bear['risks']])}
                </ul>
            </div>
            """, unsafe_allow_html=True)

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
            yaxis=dict(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)", title="Price ($)"),
            yaxis2=dict(showgrid=False, title="Volume"),
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📁 View & Download Historical Price Data"):
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)
            csv = df.to_csv().encode("utf-8")
            st.download_button(label=f"📥 Download {ticker_input} CSV Data", data=csv, file_name=f"{ticker_input}_historical_data.csv", mime="text/csv")

    with tab_ai_copilot:
        st.subheader(f"🤖 AI Market Sentiment & Intelligence for {company_name}")
        news_items = fetch_stock_news(ticker_input)

        if not news_items:
            st.info(f"No recent news articles found for {ticker_input}.")
        else:
            with st.spinner("Analyzing market sentiment from news releases..."):
                sentiment = analyze_news_sentiment(gemini_key, ticker_input, news_items, current_price, company_name)

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
                st.markdown(f"""
                <div class="news-card-styled">
                    <a href="{item['link']}" target="_blank" class="news-title-link">
                        🔗 {item['title']}
                    </a>
                    <div style="font-size: 0.84rem; opacity: 0.75; font-weight: 500;">
                        Source: <span style="color: #3b82f6; font-weight: 600;">{item['publisher']}</span> &nbsp;•&nbsp; Published: {item['time']}
                    </div>
                </div>
                """, unsafe_allow_html=True)


# Auto-refresh execution
if auto_refresh and hasattr(st, "fragment"):
    @st.fragment(run_every="15s")
    def live_container():
        render_terminal()
    live_container()
else:
    render_terminal()
