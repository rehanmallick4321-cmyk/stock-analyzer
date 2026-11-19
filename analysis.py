import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional


def fetch_stock_data(ticker_symbol: str, period: str = "1y") -> Tuple[Optional[pd.DataFrame], Optional[Dict[str, Any]], Optional[str]]:
    """
    Fetches historical OHLCV data and company fundamental information from Yahoo Finance.
    Calculates technical indicators: 20-day SMA, 50-day SMA, and 14-day RSI.
    """
    try:
        ticker = yf.Ticker(ticker_symbol.strip().upper())
        df = ticker.history(period=period)
        
        if df.empty:
            return None, None, f"No historical price data found for '{ticker_symbol}'. Check ticker symbol."
        
        # Calculate Technical Indicators
        df["SMA_20"] = df["Close"].rolling(window=20).mean()
        df["SMA_50"] = df["Close"].rolling(window=50).mean()
        
        # 14-day Relative Strength Index (RSI)
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        df["RSI_14"] = 100 - (100 / (1 + rs))

        info = ticker.info or {}
        return df, info, None
    except Exception as e:
        return None, None, f"Error fetching data: {str(e)}"


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

    # Calculate percentage spread if targets exist
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
    Generates dynamic Bull and Bear scenarios based on:
    - Wall Street price targets
    - Fundamental health (P/E ratio, profit margins, revenue growth, debt)
    - Technical momentum (price vs SMAs, RSI)
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

    # 1. Determine Target Prices
    bull_target = targets["high"] if targets["high"] else round(latest_close * 1.25, 2)
    bear_target = targets["low"] if targets["low"] else round(latest_close * 0.80, 2)
    bull_upside = ((bull_target - latest_close) / latest_close) * 100
    bear_downside = ((bear_target - latest_close) / latest_close) * 100

    # 2. Bullish Catalysts
    bull_points = []
    if revenue_growth and revenue_growth > 0:
        bull_points.append(f"Accelerating Revenue Growth: Expanding at {revenue_growth * 100:.1f}% year-over-year.")
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
        bull_points.append(f"Wall Street Consensus: Covered by {targets['opinions_count']} analysts with a general '{targets['recommendation']}' consensus.")

    # 3. Bearish Risks
    bear_points = []
    if pe and pe > 40:
        bear_points.append(f"Valuation Risk: Elevated P/E ratio ({pe:.1f}x) leaves little margin for error if earnings miss.")
    elif pe:
        bear_points.append(f"Multiple Compression: P/E is {pe:.1f}x, which could compress during market-wide risk-off shifts.")
    else:
        bear_points.append("Unprofitable or low net earnings multiple vulnerability.")

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

    bear_points.append("Sector competition and consumer/enterprise spending headwinds.")

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
