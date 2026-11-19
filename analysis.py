import yfinance as yf
import pandas as pd
import numpy as np
import requests
from typing import Dict, Any, Tuple, Optional


def fetch_stock_data(ticker_symbol: str, period: str = "1y") -> Tuple[Optional[pd.DataFrame], Optional[Dict[str, Any]], Optional[str]]:
    """
    Fetches historical OHLCV data and company fundamentals from Yahoo Finance.
    Includes custom headers and timeouts to prevent hanging on cloud servers (AWS/Streamlit Cloud).
    """
    clean_symbol = ticker_symbol.strip().upper()
    if not clean_symbol:
        return None, None, "Please enter a valid stock ticker symbol."

    try:
        # Create a session with browser-like user agent to avoid cloud IP blocking
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

        ticker = yf.Ticker(clean_symbol, session=session)
        
        # 1. Fetch historical price data with timeout protection
        df = ticker.history(period=period, timeout=10)
        
        if df is None or df.empty:
            return None, None, f"No price data found for '{clean_symbol}'. Yahoo Finance may be rate-limiting or the ticker is invalid."

        # Calculate Technical Indicators
        df["SMA_20"] = df["Close"].rolling(window=20).mean()
        df["SMA_50"] = df["Close"].rolling(window=50).mean()

        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        df["RSI_14"] = 100 - (100 / (1 + rs))

        # 2. Fetch company info safely (fallback to fast_info if info hangs or fails)
        info = {}
        try:
            info = ticker.info or {}
        except Exception:
            # Fallback to fast_info for basic attributes if full info fails
            try:
                fast = ticker.fast_info
                info = {
                    "longName": clean_symbol,
                    "marketCap": getattr(fast, "market_cap", None),
                    "fiftyTwoWeekHigh": getattr(fast, "year_high", None),
                    "fiftyTwoWeekLow": getattr(fast, "year_low", None),
                    "currency": getattr(fast, "currency", "USD"),
                }
            except Exception:
                info = {"longName": clean_symbol, "currency": "USD"}

        return df, info, None
    except Exception as e:
        return None, None, f"Failed to load data for '{clean_symbol}': {str(e)}"


def get_price_targets(info: Dict[str, Any], current_price: float) -> Dict[str, Any]:
    """
    Extracts analyst price targets and computes expected upside / downside percentages.
    """
    high = info.get("targetHighPrice")
    low = info.get("targetLowPrice")
    mean = info.get("targetMeanPrice")
    median = info.get("targetMedianPrice")
    recommendation = (info.get("recommendationKey") or "N/A").replace("_", " ").upper()
    opinions_count = info.get("numberOfAnalystOpinions", 0)

    upside_mean_pct = ((mean - current_price) / current_price * 100) if (mean and current_price) else None
    upside_high_pct = ((high - current_price) / current_price * 100) if (high and current_price) else None
    downside_low_pct = ((low - current_price) / current_price * 100) if (low and current_price) else None

    return {
        "high": high,
        "low": low,
        "mean": mean,
        "median": median,
        "recommendation": recommendation,
        "opinions_count": opinions_count,
        "upside_mean_pct": upside_mean_pct,
        "upside_high_pct": upside_high_pct,
        "downside_low_pct": downside_low_pct,
    }


def generate_scenarios(info: Dict[str, Any], df: pd.DataFrame, current_price: float, targets: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates dynamic Bull and Bear scenarios based on analyst targets and fundamental/technical metrics.
    """
    latest_close = current_price
    sma_20 = df["SMA_20"].iloc[-1] if "SMA_20" in df and not pd.isna(df["SMA_20"].iloc[-1]) else latest_close
    sma_50 = df["SMA_50"].iloc[-1] if "SMA_50" in df and not pd.isna(df["SMA_50"].iloc[-1]) else latest_close
    rsi = df["RSI_14"].iloc[-1] if "RSI_14" in df and not pd.isna(df["RSI_14"].iloc[-1]) else 50.0

    pe = info.get("trailingPE") or info.get("forwardPE")
    profit_margin = info.get("profitMargins")
    revenue_growth = info.get("revenueGrowth")
    debt_to_equity = info.get("debtToEquity")
    high_52 = info.get("fiftyTwoWeekHigh", latest_close)
    low_52 = info.get("fiftyTwoWeekLow", latest_close)

    # Targets
    bull_target = targets["high"] if targets["high"] else round(latest_close * 1.25, 2)
    bear_target = targets["low"] if targets["low"] else round(latest_close * 0.80, 2)
    bull_upside = ((bull_target - latest_close) / latest_close) * 100
    bear_downside = ((bear_target - latest_close) / latest_close) * 100

    # Bullish Catalysts
    bull_points = []
    if revenue_growth and revenue_growth > 0:
        bull_points.append(f"Accelerating Revenue Growth: Expanding at {revenue_growth * 100:.1f}% YoY.")
    else:
        bull_points.append("Core product stability and defensive cash-flow generation.")

    if profit_margin and profit_margin > 0.15:
        bull_points.append(f"High Profitability: Robust net profit margins of {profit_margin * 100:.1f}%.")
    else:
        bull_points.append("Margin expansion potential through operational efficiency.")

    if latest_close >= sma_50:
        bull_points.append(f"Bullish Trend: Holding firmly above the 50-day moving average (${sma_50:.2f}).")
    elif rsi < 35:
        bull_points.append(f"Oversold Bounce: RSI is at {rsi:.1f}, indicating high potential for mean-reversion rally.")
    else:
        bull_points.append(f"Technical momentum testing resistance near 52-week high of ${high_52:.2f}.")

    if targets["opinions_count"] and targets["opinions_count"] > 5:
        bull_points.append(f"Wall Street Consensus: Covered by {targets['opinions_count']} analysts with a '{targets['recommendation']}' consensus.")

    # Bearish Risks
    bear_points = []
    if pe and pe > 40:
        bear_points.append(f"Valuation Risk: Elevated P/E ratio ({pe:.1f}x) leaves little margin for error.")
    elif pe:
        bear_points.append(f"Multiple Compression: P/E is {pe:.1f}x, which could compress during risk-off market shifts.")
    else:
        bear_points.append("Vulnerability to earnings multiple contraction.")

    if debt_to_equity and debt_to_equity > 150:
        bear_points.append(f"Leverage Concerns: Elevated Debt-to-Equity ratio of {debt_to_equity:.1f}%.")
    else:
        bear_points.append("Vulnerability to higher-for-longer interest rates and macro liquidity tightening.")

    if latest_close < sma_50:
        bear_points.append(f"Technical Breakdown: Trading below the critical 50-day moving average (${sma_50:.2f}).")
    elif rsi > 70:
        bear_points.append(f"Overbought Territory: RSI is at {rsi:.1f}, signaling elevated risk of short-term pullback.")
    else:
        bear_points.append(f"Downside buffer risk towards 52-week support around ${low_52:.2f}.")

    return {
        "bull": {
            "target": bull_target,
            "upside_pct": bull_upside,
            "catalysts": bull_points[:4],
        },
        "bear": {
            "target": bear_target,
            "downside_pct": bear_downside,
            "risks": bear_points[:4],
        },
    }
