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

# 1. Page Configuration
st.set_page_config(
    page_title="APEX TRADER // Pro Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",  # Clean mobile-first default
)

# Mobile-First Professional Trader UI Styling
st.markdown("""
<style>
    /* Trader Terminal Styling */
    .trader-brand {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 12px;
    }
    .terminal-badge {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        background: rgba(59, 130, 246, 0.15);
        color: #3b82f6;
        padding: 4px 10px;
        border-radius: 6px;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    /* Mobile responsive optimizations */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 0.75rem !important;
            padding-bottom: 1.5rem !important;
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
        }
        h1 {
            font-size: 1.5rem !important;
            line-height: 1.2 !important;
        }
        h2, h3 {
            font-size: 1.2rem !important;
        }
        [data-testid="column"] {
            min-width: 48% !important;
            margin-bottom: 6px !important;
        }
        .stMetric {
            padding: 4px !important;
        }
        .stMetric div[data-testid="stMetricValue"] {
            font-size: 1.35rem !important;
        }
    }

    /* Plotly mobile touch protection */
    .js-plotly-plot {
        touch-action: pan-y !important;
    }
</style>
""", unsafe_allow_html=True)

# 2. Trader Terminal Header
st.markdown("""
<div class="trader-brand">
    <div>
        <h2 style="margin: 0; font-size: 1.6rem; font-weight: 900; letter-spacing: -0.03em;">
            ⚡ APEX TRADER <span style="font-weight: 400; opacity: 0.75; font-size: 1.1rem;">// PRO TERMINAL</span>
        </h2>
        <div style="font-size: 0.75rem; opacity: 0.7; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; margin-top: 2px;">
            Institutional Equity Feed & AI Quantitative Risk Engine
        </div>
    </div>
    <div>
        <span class="terminal-badge">LIVE DESK v2.6</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 3. Horizontal Mobile-First Search & Control Bar
# Trader Quick Catalogs
INDIAN_STOCKS = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "TATAMOTORS", "ITC", "ICICIBANK", "SBIN", "BHARTIARTL", "ZOMATO"]
US_STOCKS = ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN", "GOOGL", "META"]

if "search_query" not in st.session_state:
    st.session_state.search_query = "RELIANCE"

with st.container(border=True):
    # Row 1: Exchange selector + Search Input
    c_exch, c_search = st.columns([1, 2])
    with c_exch:
        market_choice = st.radio(
            "Exchange",
            ["🇮🇳 NSE (India)", "🇺🇸 US (NASDAQ/NYSE)"],
            horizontal=True,
            label_visibility="collapsed",
        )
    with c_search:
        searched_val = st.text_input(
            "Ticker Search",
            value=st.session_state.search_query,
            placeholder="🔍 Enter ticker (e.g. RELIANCE, TCS, NVDA, TSLA...)",
            label_visibility="collapsed",
        ).strip().upper()

    # Row 2: 1-Tap Quick Watchlist Chips (Horizontal Pills)
    current_catalog = INDIAN_STOCKS if "NSE" in market_choice else US_STOCKS
    
    # Handle user clicking quick chips
    selected_chip = st.pills(
        "Hot Watchlist:",
        current_catalog,
        selection_mode="single",
        label_visibility="collapsed",
    )
    if selected_chip and selected_chip != st.session_state.search_query:
        st.session_state.search_query = selected_chip
        st.rerun()

    # Row 3: Horizontal Period Pills + Chart Style + Indicators
    c_p1, c_p2, c_p3 = st.columns([2, 1, 1])
    with c_p1:
        timeframe_label = st.segmented_control(
            "Period",
            ["1M", "3M", "6M", "1Y", "2Y", "5Y"],
            default="1Y",
            label_visibility="collapsed",
        ) or "1Y"
        # Map label to yfinance period
        period_map = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "2Y": "2y", "5Y": "5y"}
        timeframe = period_map.get(timeframe_label, "1y")

    with c_p2:
        chart_style = st.segmented_control(
            "Style",
            ["🕯️ Candles", "📈 Line"],
            default="🕯️ Candles",
            label_visibility="collapsed",
        ) or "🕯️ Candles"
        chart_type = "Candlestick" if "Candles" in chart_style else "Line"

    with c_p3:
        show_sma = st.checkbox("SMA 20/50", value=True)

# Format ticker symbol
active_base = searched_val if searched_val else ("RELIANCE" if "NSE" in market_choice else "NVDA")
if "NSE" in market_choice:
    if not active_base.endswith(".NS") and not active_base.endswith(".BO"):
        ticker_input = f"{active_base}.NS"
    else:
        ticker_input = active_base
else:
    ticker_input = active_base

# 4. Sidebar: Optional Advanced Settings
st.sidebar.markdown("### ⚙️ Terminal Settings")
auto_refresh = st.sidebar.toggle("Auto-Refresh Market (15s)", value=False)

secrets_api_key = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""
gemini_key_input = st.sidebar.text_input(
    "Google Gemini Key (optional):",
    value=secrets_api_key,
    type="password",
    help="Get a free key from aistudio.google.com to power AI sentiment reasoning.",
)
gemini_key = gemini_key_input.strip() or secrets_api_key

# 5. Market Session Status
market_info = get_market_status(ticker_input)

# 6. Data Loading
@st.cache_data(ttl=15 if auto_refresh else 300, show_spinner=False)
def load_data(symbol: str, period: str):
    return fetch_stock_data(symbol, period)

def render_terminal():
    with st.spinner(f"Connecting to live feed for {ticker_input}..."):
        try:
            df, info, err = load_data(ticker_input, timeframe)
        except Exception as e:
            df, info, err = None, None, f"Error: {e}"

    if err or df is None or info is None or df.empty:
        st.error(f"⚠️ {err or 'Unable to load data. Please check ticker symbol.'}")
        if "NSE" in market_choice:
            st.info("Tip for Indian stocks: Enter symbols like RELIANCE, TCS, INFY, HDFCBANK, or TATAMOTORS.")
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

    # Top Status Pill
    status_icon = "🟢" if active_session == "REGULAR" else ("🟡" if active_session == "PRE" else ("🌙" if active_session == "POST" else "🔴"))
    st.info(f"{status_icon} **{market_info['badge']}** &nbsp;•&nbsp; {market_info['details']}")

    # Standardized Company & Ticker Header
    st.title(f"🏛️ {company_name}")
    st.caption(
        f"**`{meta['flag']} {meta['standard_display']}`** &nbsp;|&nbsp; "
        f"Exchange: **{meta['exchange_name']}** &nbsp;|&nbsp; "
        f"Currency: **{currency} ({curr_sym})** &nbsp;|&nbsp; "
        f"Sector: **{sector}**"
    )

    st.write("")

    # --- COMPACT SESSION PRICING ---
    if active_session == "PRE" and ext_data["pre_price"]:
        c_reg, c_pre = st.columns(2)
        with c_reg:
            with st.container(border=True):
                st.metric(
                    label=f"🏢 Regular Close ({meta['standard_display']})",
                    value=f"{curr_sym}{current_price:,.2f}",
                    delta=f"{day_change:+,.2f} ({day_change_pct:+.2f}%)",
                )
        with c_pre:
            with st.container(border=True):
                pre_change = ext_data["pre_change"] or 0.0
                pre_pct = ext_data["pre_pct"] or 0.0
                st.metric(
                    label="🌅 PRE-MARKET (LIVE NOW)",
                    value=f"{curr_sym}{ext_data['pre_price']:,.2f}",
                    delta=f"{pre_change:+,.2f} ({pre_pct:+.2f}%) vs Close",
                )
    elif active_session == "POST" and ext_data["post_price"]:
        c_reg, c_post = st.columns(2)
        with c_reg:
            with st.container(border=True):
                st.metric(
                    label=f"🏢 Regular Close ({meta['standard_display']})",
                    value=f"{curr_sym}{current_price:,.2f}",
                    delta=f"{day_change:+,.2f} ({day_change_pct:+.2f}%)",
                )
        with c_post:
            with st.container(border=True):
                post_change = ext_data["post_change"] or 0.0
                post_pct = ext_data["post_pct"] or 0.0
                st.metric(
                    label="🌙 AFTER-HOURS (LIVE NOW)",
                    value=f"{curr_sym}{ext_data['post_price']:,.2f}",
                    delta=f"{post_change:+,.2f} ({post_pct:+.2f}%) vs Close",
                )
    else:
        with st.container(border=True):
            reg_badge = "🟢 LIVE TRADING SESSION" if active_session == "REGULAR" else "🏢 REGULAR MARKET CLOSE"
            st.metric(
                label=f"{reg_badge} ({meta['standard_display']})",
                value=f"{curr_sym}{current_price:,.2f}",
                delta=f"{day_change:+,.2f} ({day_change_pct:+.2f}%)",
            )
        
        # Collapse extended hours during closed hours to save mobile space
        if ext_data["pre_price"] or ext_data["post_price"]:
            with st.expander("⏱️ View Extended Hours Data (Pre & Post Market)", expanded=False):
                exp_c1, exp_c2 = st.columns(2)
                with exp_c1:
                    if ext_data["pre_price"]:
                        p_ch = ext_data["pre_change"] or 0.0
                        p_pc = ext_data["pre_pct"] or 0.0
                        st.metric("🌅 Pre-Market Recorded", f"{curr_sym}{ext_data['pre_price']:,.2f}", f"{p_ch:+,.2f} ({p_pc:+.2f}%)")
                    else:
                        st.caption("No pre-market quote recorded for this session.")
                with exp_c2:
                    if ext_data["post_price"]:
                        po_ch = ext_data["post_change"] or 0.0
                        po_pc = ext_data["post_pct"] or 0.0
                        st.metric("🌙 After-Hours Recorded", f"{curr_sym}{ext_data['post_price']:,.2f}", f"{po_ch:+,.2f} ({po_pc:+.2f}%)")
                    else:
                        st.caption("No post-market quote recorded for this session.")

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
    k1.metric("Market Cap", mcap_str)
    k2.metric("P/E Ratio", pe_str)
    k3.metric("52-Week High", high_str)
    k4.metric("52-Week Low", low_str)

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
                height=130,
                margin=dict(l=10, r=10, t=25, b=25),
                xaxis=dict(showgrid=True, title=f"Price ({currency})", zeroline=False),
                yaxis=dict(showticklabels=False),
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="gray"),
            )
            st.plotly_chart(
                fig_target,
                use_container_width=True,
                config={'displayModeBar': False, 'scrollZoom': False, 'responsive': True}
            )

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
            height=480,
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="gray"),
            xaxis=dict(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)"),
            yaxis=dict(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)", title=f"Price ({curr_sym})"),
            yaxis2=dict(showgrid=False, title="Volume"),
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                'scrollZoom': False,
                'displayModeBar': False,
                'responsive': True,
            }
        )

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
                fig_gauge.update_layout(height=240, margin=dict(l=10, r=10, t=35, b=10), paper_bgcolor="rgba(0,0,0,0)", font=dict(color="gray"))
                st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False, 'responsive': True})

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
