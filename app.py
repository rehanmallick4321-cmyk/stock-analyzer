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
    initial_sidebar_state="collapsed",
)

# 2. Ultra-Tight Padding & Mobile-First Styling
st.markdown("""
<style>
    /* Ultra-tight block-container padding */
    .block-container {
        padding-top: 0.25rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
        max-width: 100% !important;
    }
    
    /* Header brand */
    .brand-title {
        font-size: 1.35rem;
        font-weight: 900;
        letter-spacing: -0.02em;
        margin: 0;
        line-height: 1.2;
    }
    
    /* Compact Market Status Pill */
    .compact-market-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 6px;
        background-color: var(--secondary-background-color, #1e293b);
        border: 1px solid rgba(148, 163, 184, 0.2);
        color: var(--text-color, #f8fafc);
        margin: 2px 0 8px 0;
    }

    /* Segmented Control Breathing Room & Anti-Clipping */
    [data-testid="stSegmentedControl"] {
        min-width: 100% !important;
    }
    [data-testid="stSegmentedControl"] [role="radiogroup"] {
        gap: 3px !important;
        padding: 2px 3px !important;
    }
    [data-testid="stSegmentedControl"] button {
        padding-left: 9px !important;
        padding-right: 9px !important;
        font-size: 0.81rem !important;
        text-overflow: clip !important;
        overflow: visible !important;
    }

    /* Bloomberg / TradingView Styled Badges */
    .tv-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace, sans-serif;
    }
    .tv-badge-ticker {
        background-color: rgba(59, 130, 246, 0.12);
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.25);
    }
    .tv-badge-live {
        background-color: rgba(34, 197, 94, 0.12);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.25);
    }
    .tv-badge-closed {
        background-color: rgba(148, 163, 184, 0.12);
        color: #94a3b8;
        border: 1px solid rgba(148, 163, 184, 0.25);
    }
    .tv-badge-pre {
        background-color: rgba(234, 179, 8, 0.12);
        color: #eab308;
        border: 1px solid rgba(234, 179, 8, 0.25);
    }
    .tv-badge-post {
        background-color: rgba(168, 85, 247, 0.12);
        color: #a855f7;
        border: 1px solid rgba(168, 85, 247, 0.25);
    }

    /* Mobile Responsive Column Tiling */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 0.15rem !important;
            padding-left: 0.4rem !important;
            padding-right: 0.4rem !important;
        }
        .brand-title {
            font-size: 1.15rem !important;
        }
        [data-testid="column"] {
            min-width: 48% !important;
            margin-bottom: 4px !important;
        }
        .stMetric {
            padding: 2px !important;
        }
        .stMetric label {
            font-size: 0.75rem !important;
        }
        .stMetric div[data-testid="stMetricValue"] {
            font-size: 1.25rem !important;
        }
    }

    /* Prevent mobile chart touch capture */
    .js-plotly-plot {
        touch-action: pan-y !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Top Compact Brand Header
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
    <div>
        <span class="brand-title">⚡ APEX TRADER <span style="font-size: 0.88rem; font-weight: 500; opacity: 0.7;">// PRO TERMINAL</span></span>
    </div>
</div>
""", unsafe_allow_html=True)

# 4. Standardized Watchlist Catalog
INDIAN_STOCKS = {
    "RELIANCE": "RELIANCE • Reliance Industries",
    "TCS": "TCS • Tata Consultancy Services",
    "HDFCBANK": "HDFCBANK • HDFC Bank",
    "INFY": "INFY • Infosys Limited",
    "TATAMOTORS": "TATAMOTORS • Tata Motors",
    "ITC": "ITC • ITC Limited",
    "ICICIBANK": "ICICIBANK • ICICI Bank",
    "SBIN": "SBIN • State Bank of India",
    "BHARTIARTL": "BHARTIARTL • Bharti Airtel",
    "ZOMATO": "ZOMATO • Zomato Limited",
    "LICI": "LICI • Life Insurance Corp",
    "HINDUNILVR": "HINDUNILVR • Hindustan Unilever",
    "MARUTI": "MARUTI • Maruti Suzuki",
    "BAJFINANCE": "BAJFINANCE • Bajaj Finance",
    "CUSTOM": "✍️ Custom Symbol...",
}

US_STOCKS = {
    "NVDA": "NVDA • NVIDIA Corporation",
    "AAPL": "AAPL • Apple Inc",
    "MSFT": "MSFT • Microsoft Corporation",
    "TSLA": "TSLA • Tesla Inc",
    "AMZN": "AMZN • Amazon.com Inc",
    "GOOGL": "GOOGL • Alphabet Inc",
    "META": "META • Meta Platforms",
    "AMD": "AMD • Advanced Micro Devices",
    "NFLX": "NFLX • Netflix Inc",
    "CUSTOM": "✍️ Custom Symbol...",
}

# 5. Horizontal Top Control Toolbar (Including Horizontal Live Auto-Refresh)
with st.container(border=True):
    col_mkt, col_select, col_period, col_style, col_refresh = st.columns([1.3, 2.2, 1.7, 1.45, 1.25])

    with col_mkt:
        market_choice = st.segmented_control(
            "Market",
            ["🇮🇳 NSE", "🇺🇸 US"],
            default="🇮🇳 NSE",
            label_visibility="collapsed",
        ) or "🇮🇳 NSE"

    catalog = INDIAN_STOCKS if "NSE" in market_choice else US_STOCKS
    catalog_keys = list(catalog.keys())
    catalog_labels = list(catalog.values())

    with col_select:
        selected_label = st.selectbox(
            "Ticker Select",
            catalog_labels,
            index=0,
            label_visibility="collapsed",
        )
        selected_key = [k for k, v in catalog.items() if v == selected_label][0]

        if selected_key == "CUSTOM":
            custom_input = st.text_input("Enter Ticker:", value="WIPRO" if "NSE" in market_choice else "PLTR", label_visibility="collapsed").strip().upper()
            active_ticker_base = custom_input
        else:
            active_ticker_base = selected_key

    with col_period:
        timeframe_label = st.segmented_control(
            "Period",
            ["1M", "3M", "6M", "1Y", "2Y", "5Y"],
            default="1Y",
            label_visibility="collapsed",
        ) or "1Y"
        period_map = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "2Y": "2y", "5Y": "5y"}
        timeframe = period_map.get(timeframe_label, "1y")

    with col_style:
        chart_style = st.segmented_control(
            "Style",
            ["🕯️ Candles", "📈 Line"],
            default="🕯️ Candles",
            label_visibility="collapsed",
        ) or "🕯️ Candles"
        chart_type = "Candlestick" if "Candles" in chart_style else "Line"

    with col_refresh:
        # Compact label and wider ratio to prevent any truncation with '...'
        auto_refresh = st.toggle("⚡ Live", value=False, help="Auto-refresh prices and charts every 15 seconds")

# Format ticker with exchange suffix
if "NSE" in market_choice:
    if not active_ticker_base.endswith(".NS") and not active_ticker_base.endswith(".BO"):
        ticker_input = f"{active_ticker_base}.NS"
    else:
        ticker_input = active_ticker_base
else:
    ticker_input = active_ticker_base

# 6. Sidebar: Advanced Settings & Indicators
st.sidebar.markdown("### ⚙️ Terminal Settings")
show_sma = st.sidebar.checkbox("Show 20 & 50-Day Moving Averages", value=True)

secrets_api_key = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""
gemini_key_input = st.sidebar.text_input(
    "Google Gemini Key (optional):",
    value=secrets_api_key,
    type="password",
    help="Get a free key from aistudio.google.com to power AI sentiment reasoning.",
)
gemini_key = gemini_key_input.strip() or secrets_api_key

# 7. Market Session Status (Shortened, Clean TradingView-style Pill)
market_info = get_market_status(ticker_input)
active_session = market_info.get("session", "REGULAR")
clean_badge = market_info.get("badge", "").replace("🔴", "").replace("🟢", "").replace("🟡", "").replace("🌙", "").strip()
pill_status = "LIVE" if active_session == "REGULAR" else ("PRE-MKT" if active_session == "PRE" else ("POST-MKT" if active_session == "POST" else "CLOSED"))
pill_cls = "tv-badge-live" if active_session == "REGULAR" else ("tv-badge-pre" if active_session == "PRE" else ("tv-badge-post" if active_session == "POST" else "tv-badge-closed"))

st.markdown(f"""
<div class="compact-market-pill">
    <span class="tv-badge {pill_cls}" style="font-size: 0.68rem; padding: 1px 6px;">{pill_status}</span>
    <span><b>{clean_badge}</b></span>
    <span style="opacity: 0.4;">•</span>
    <span style="opacity: 0.85;">{market_info.get('details', '')}</span>
</div>
""", unsafe_allow_html=True)

# 8. Data Loading
@st.cache_data(ttl=15 if auto_refresh else 300, show_spinner=False)
def load_data(symbol: str, period: str):
    return fetch_stock_data(symbol, period)

def render_terminal():
    with st.spinner(f"Fetching {ticker_input}..."):
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
    currency = (info.get("currency") or ("INR" if ticker_input.endswith(".NS") or ticker_input.endswith(".BO") else "USD")).upper()
    curr_sym = "₹" if currency == "INR" else ("€" if currency == "EUR" else ("£" if currency == "GBP" else "$"))
    sector = info.get("sector", "N/A")
    meta = format_ticker_metadata(ticker_input, info)

    # Pre/Post market data
    ext_data = get_pre_post_market(info, current_price)

    # Bloomberg / TradingView Styled Clean Header (No emojis)
    hdr_status = "LIVE" if active_session == "REGULAR" else ("PRE-MARKET" if active_session == "PRE" else ("AFTER-HOURS" if active_session == "POST" else "CLOSED"))
    hdr_cls = "tv-badge-live" if active_session == "REGULAR" else ("tv-badge-pre" if active_session == "PRE" else ("tv-badge-post" if active_session == "POST" else "tv-badge-closed"))

    st.markdown(f"""
    <div style="display: flex; align-items: baseline; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin: 4px 0 6px 0;">
        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
            <span style="font-size: 1.35rem; font-weight: 800; letter-spacing: -0.02em;">{company_name}</span>
            <span class="tv-badge tv-badge-ticker">{meta['standard_display']}</span>
            <span class="tv-badge {hdr_cls}">{hdr_status}</span>
        </div>
        <div style="font-size: 0.8rem; opacity: 0.7; font-weight: 500;">
            {sector} &nbsp;•&nbsp; Currency: <b>{currency} ({curr_sym})</b> &nbsp;•&nbsp; <b>{meta['exchange_name']}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Live Price Hero Card (Bloomberg/TradingView Clean Badges: e.g. "NASDAQ: NVDA • CLOSED") ---
    if active_session == "PRE" and ext_data["pre_price"]:
        c_reg, c_ext = st.columns(2)
        with c_reg:
            with st.container(border=True):
                st.metric(f"{meta['standard_display']} • REGULAR CLOSE", f"{curr_sym}{current_price:,.2f}", f"{day_change:+,.2f} ({day_change_pct:+.2f}%)")
        with c_ext:
            with st.container(border=True):
                pre_ch = ext_data["pre_change"] or 0.0
                pre_pc = ext_data["pre_pct"] or 0.0
                st.metric(f"{meta['standard_display']} • PRE-MARKET", f"{curr_sym}{ext_data['pre_price']:,.2f}", f"{pre_ch:+,.2f} ({pre_pc:+.2f}%) vs Close")
    elif active_session == "POST" and ext_data["post_price"]:
        c_reg, c_ext = st.columns(2)
        with c_reg:
            with st.container(border=True):
                st.metric(f"{meta['standard_display']} • REGULAR CLOSE", f"{curr_sym}{current_price:,.2f}", f"{day_change:+,.2f} ({day_change_pct:+.2f}%)")
        with c_ext:
            with st.container(border=True):
                post_ch = ext_data["post_change"] or 0.0
                post_pc = ext_data["post_pct"] or 0.0
                st.metric(f"{meta['standard_display']} • AFTER-HOURS", f"{curr_sym}{ext_data['post_price']:,.2f}", f"{post_ch:+,.2f} ({post_pc:+.2f}%) vs Close")
    else:
        with st.container(border=True):
            hero_session_label = "LIVE" if active_session == "REGULAR" else "CLOSED"
            st.metric(
                label=f"{meta['standard_display']} • {hero_session_label}",
                value=f"{curr_sym}{current_price:,.2f}",
                delta=f"{day_change:+,.2f} ({day_change_pct:+.2f}%)",
            )
        
        # Collapsed expander for extended hours during closed sessions
        if ext_data["pre_price"] or ext_data["post_price"]:
            with st.expander("⏱️ View Extended Hours (Pre / Post Market)", expanded=False):
                ec1, ec2 = st.columns(2)
                with ec1:
                    if ext_data["pre_price"]:
                        st.metric(f"{meta['standard_display']} • Pre-Market", f"{curr_sym}{ext_data['pre_price']:,.2f}", f"{ext_data['pre_change'] or 0.0:+,.2f} ({ext_data['pre_pct'] or 0.0:+.2f}%)")
                    else:
                        st.caption("No pre-market quote recorded.")
                with ec2:
                    if ext_data["post_price"]:
                        st.metric(f"{meta['standard_display']} • After-Hours", f"{curr_sym}{ext_data['post_price']:,.2f}", f"{ext_data['post_change'] or 0.0:+,.2f} ({ext_data['post_pct'] or 0.0:+.2f}%)")
                    else:
                        st.caption("No post-market quote recorded.")

    # --- 6-PACK HIGH-IMPACT KPI METRIC CARDS (UNIFORM VISUAL SYMMETRY) ---
    pe_ratio = info.get("trailingPE") or info.get("forwardPE")
    forward_pe = info.get("forwardPE")
    market_cap = info.get("marketCap")
    
    if market_cap:
        if currency == "INR":
            mcap_str = f"₹{market_cap / 1e12:.2f} Lakh Cr" if market_cap >= 1e12 else f"₹{market_cap / 1e7:,.0f} Cr"
            cap_badge = "Large Cap" if market_cap >= 2e11 else ("Mid Cap" if market_cap >= 5e10 else "Small Cap")
        else:
            mcap_str = f"${market_cap / 1e12:.2f}T" if market_cap >= 1e12 else f"${market_cap / 1e9:.2f}B"
            cap_badge = "Mega Cap" if market_cap >= 2e11 else ("Large Cap" if market_cap >= 1e10 else "Mid Cap")
    else:
        mcap_str = "N/A"
        cap_badge = None

    pe_str = f"{pe_ratio:.1f}x" if pe_ratio else "N/A"
    week_52_high = info.get("fiftyTwoWeekHigh")
    week_52_low = info.get("fiftyTwoWeekLow")
    high_str = f"{curr_sym}{week_52_high:,.2f}" if week_52_high else "N/A"
    low_str = f"{curr_sym}{week_52_low:,.2f}" if week_52_low else "N/A"

    # Subtle helper badges under 52W High and 52W Low (% from High / % from Low) for visual symmetry
    if week_52_high and current_price:
        pct_from_high = ((current_price - week_52_high) / week_52_high) * 100
        high_delta = f"{pct_from_high:+.1f}% from High"
    else:
        high_delta = None

    if week_52_low and current_price:
        pct_from_low = ((current_price - week_52_low) / week_52_low) * 100
        low_delta = f"{pct_from_low:+.1f}% from Low"
    else:
        low_delta = None

    # Volume & Technicals
    latest_vol = df["Volume"].iloc[-1] if "Volume" in df and len(df) > 0 else 0
    avg_vol = info.get("averageVolume") or info.get("averageDailyVolume10Day") or latest_vol
    vol_str = f"{latest_vol / 1e6:.1f}M" if latest_vol >= 1e6 else (f"{latest_vol / 1e3:.0f}K" if latest_vol >= 1e3 else str(latest_vol))
    avg_vol_str = f"{avg_vol / 1e6:.1f}M" if avg_vol >= 1e6 else (f"{avg_vol / 1e3:.0f}K" if avg_vol >= 1e3 else str(avg_vol))

    rsi_val = df["RSI_14"].iloc[-1] if "RSI_14" in df and not pd.isna(df["RSI_14"].iloc[-1]) else 50.0
    rsi_tag = "Overbought" if rsi_val > 70 else ("Oversold" if rsi_val < 30 else "Neutral")

    # Render KPI Cards Grid (All 6 columns have uniform height & delta badges)
    with st.container(border=True):
        st.markdown("<div style='font-size:0.78rem; font-weight:700; text-transform:uppercase; opacity:0.75; margin-bottom:4px;'>📊 Key Valuation & Risk KPIs</div>", unsafe_allow_html=True)
        kp1, kp2, kp3, kp4, kp5, kp6 = st.columns(6)
        kp1.metric("Market Cap", mcap_str, cap_badge, delta_color="off")
        kp2.metric("P/E Ratio", pe_str, f"Fwd: {forward_pe:.1f}x" if forward_pe else None, delta_color="off")
        kp3.metric("52W High", high_str, high_delta, delta_color="off")
        kp4.metric("52W Low", low_str, low_delta, delta_color="off")
        kp5.metric("Day Volume", vol_str, f"Avg: {avg_vol_str}", delta_color="off")
        kp6.metric("RSI (14D)", f"{rsi_val:.1f}", rsi_tag, delta_color="inverse" if rsi_val > 70 else "normal")

    st.write("")

    # --- Navigation Tabs ---
    tab_analysis, tab_ai_copilot = st.tabs(["📈 Market Analytics & Scenarios", "🤖 AI News Sentiment Copilot"])

    with tab_analysis:
        targets = get_price_targets(info, current_price)
        st.subheader("🎯 Analyst Consensus & Targets")

        tc1, tc2, tc3, tc4 = st.columns(4)
        tc1.metric("Analyst Low", f"{curr_sym}{targets['low']:,.2f}" if targets["low"] else "N/A", delta=f"{targets['downside_low_pct']:+.1f}%" if targets["downside_low_pct"] else None, delta_color="inverse")
        tc2.metric("Consensus Mean", f"{curr_sym}{targets['mean']:,.2f}" if targets["mean"] else "N/A", delta=f"{targets['upside_mean_pct']:+.1f}%" if targets["upside_mean_pct"] else None)
        tc3.metric("Analyst High", f"{curr_sym}{targets['high']:,.2f}" if targets["high"] else "N/A", delta=f"{targets['upside_high_pct']:+.1f}%" if targets["upside_high_pct"] else None)
        tc4.metric("Consensus Rating", targets["recommendation"], f"{targets['opinions_count']} analysts reporting", delta_color="off")

        # Visual Spread Chart
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
            fig_target.add_trace(go.Scatter(x=[targets["low"]], y=["Price Range"], mode="markers+text", name="Low", text=[f"Low {curr_sym}{targets['low']:.0f}"], textposition="bottom center", marker=dict(color="#EF4444", size=13, symbol="diamond")))
            fig_target.add_trace(go.Scatter(x=[current_price], y=["Price Range"], mode="markers+text", name="Current", text=[f"Current {curr_sym}{current_price:,.2f}"], textposition="top center", marker=dict(color="#3B82F6", size=15, symbol="circle", line=dict(color="#ffffff", width=2))))
            fig_target.add_trace(go.Scatter(x=[targets["mean"]], y=["Price Range"], mode="markers+text", name="Mean", text=[f"Mean {curr_sym}{targets['mean']:.0f}"], textposition="bottom center", marker=dict(color="#F59E0B", size=13, symbol="triangle-up")))
            fig_target.add_trace(go.Scatter(x=[targets["high"]], y=["Price Range"], mode="markers+text", name="High", text=[f"High {curr_sym}{targets['high']:.0f}"], textposition="bottom center", marker=dict(color="#10B981", size=13, symbol="diamond")))
            fig_target.update_layout(
                height=125,
                margin=dict(l=10, r=10, t=20, b=20),
                xaxis=dict(showgrid=True, title=f"Price ({currency})", zeroline=False),
                yaxis=dict(showticklabels=False),
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="gray"),
            )
            st.plotly_chart(fig_target, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False, 'responsive': True})

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
            fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Close", line=dict(color="#3B82F6", width=2.5)), row=1, col=1)

        if show_sma:
            if "SMA_20" in df:
                fig.add_trace(go.Scatter(x=df.index, y=df["SMA_20"], mode="lines", name="20 SMA", line=dict(color="#F59E0B", width=1.5)), row=1, col=1)
            if "SMA_50" in df:
                fig.add_trace(go.Scatter(x=df.index, y=df["SMA_50"], mode="lines", name="50 SMA", line=dict(color="#8B5CF6", width=1.5)), row=1, col=1)

        vol_colors = ["#EF4444" if r["Open"] > r["Close"] else "#10B981" for _, r in df.iterrows()]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=vol_colors, name="Volume", opacity=0.6), row=2, col=1)

        fig.update_layout(
            height=460,
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
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': False, 'displayModeBar': False, 'responsive': True})

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
