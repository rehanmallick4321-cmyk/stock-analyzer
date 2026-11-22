import yfinance as yf
import pandas as pd
import numpy as np
import requests
import datetime
import pytz
import json
from typing import Dict, Any, Tuple, Optional, List


def format_ticker_metadata(ticker_symbol: str, info: Dict[str, Any]) -> Dict[str, str]:
    """
    Standardizes ticker symbols into professional financial terminal format
    (e.g., 'NSE: RELIANCE' or 'NASDAQ: NVDA') with country flags and exchange badges.
    """
    clean_sym = ticker_symbol.strip().upper()
    exchange = (info.get("exchange") or "").upper()

    if clean_sym.endswith(".NS"):
        base = clean_sym[:-3]
        return {
            "base_symbol": base,
            "standard_display": f"NSE: {base}",
            "exchange_name": "National Stock Exchange of India (NSE)",
            "flag": "🇮🇳",
            "market_tag": "INDIAN EQUITIES",
        }
    elif clean_sym.endswith(".BO"):
        base = clean_sym[:-3]
        return {
            "base_symbol": base,
            "standard_display": f"BSE: {base}",
            "exchange_name": "Bombay Stock Exchange (BSE)",
            "flag": "🇮🇳",
            "market_tag": "INDIAN EQUITIES",
        }
    else:
        # Detect US exchange
        exch_label = "NASDAQ" if "NMS" in exchange or "NGS" in exchange or "NASDAQ" in exchange else ("NYSE" if "NYQ" in exchange or "NYSE" in exchange else "US")
        return {
            "base_symbol": clean_sym,
            "standard_display": f"{exch_label}: {clean_sym}",
            "exchange_name": f"{exch_label} (United States)",
            "flag": "🇺🇸",
            "market_tag": "US EQUITIES",
        }


def get_market_status(ticker_symbol: str = "") -> Dict[str, Any]:
    """
    Determines whether the market for the specified stock is currently open.
    Supports both Indian Exchanges (NSE/BSE via Asia/Kolkata) and US Exchanges (NYSE/NASDAQ via America/New_York).
    """
    clean_sym = ticker_symbol.strip().upper()
    is_indian_stock = clean_sym.endswith(".NS") or clean_sym.endswith(".BO")

    if is_indian_stock:
        ist_tz = pytz.timezone("Asia/Kolkata")
        now_ist = datetime.datetime.now(ist_tz)
        weekday = now_ist.weekday()

        is_weekend = weekday >= 5
        current_time = now_ist.time()
        market_open = datetime.time(9, 15)
        market_close = datetime.time(15, 30)
        pre_open = datetime.time(9, 0)
        post_close = datetime.time(16, 0)

        if is_weekend:
            return {
                "session": "CLOSED",
                "badge": "🔴 NSE/BSE Closed (Weekend)",
                "color": "#EF4444",
                "details": f"Opens Monday 9:15 AM IST (Current: {now_ist.strftime('%a %I:%M %p IST')})",
            }
        elif market_open <= current_time < market_close:
            return {
                "session": "REGULAR",
                "badge": "🟢 NSE/BSE Market LIVE",
                "color": "#10B981",
                "details": f"Trading until 3:30 PM IST (Current: {now_ist.strftime('%I:%M %p IST')})",
            }
        elif pre_open <= current_time < market_open:
            return {
                "session": "PRE",
                "badge": "🟡 NSE Pre-Market Auction",
                "color": "#F59E0B",
                "details": f"Regular bell 9:15 AM IST (Current: {now_ist.strftime('%I:%M %p IST')})",
            }
        elif market_close <= current_time < post_close:
            return {
                "session": "POST",
                "badge": "🌙 Post-Market Closing Session",
                "color": "#8B5CF6",
                "details": f"Closes 4:00 PM IST (Current: {now_ist.strftime('%I:%M %p IST')})",
            }
        else:
            return {
                "session": "CLOSED",
                "badge": "🔴 NSE/BSE Market Closed",
                "color": "#64748B",
                "details": f"Opens 9:15 AM IST (Current: {now_ist.strftime('%I:%M %p IST')})",
            }
    else:
        et_tz = pytz.timezone("America/New_York")
        now_et = datetime.datetime.now(et_tz)
        weekday = now_et.weekday()

        is_weekend = weekday >= 5
        current_time = now_et.time()
        market_open = datetime.time(9, 30)
        market_close = datetime.time(16, 0)
        pre_open = datetime.time(4, 0)
        after_close = datetime.time(20, 0)

        if is_weekend:
            return {
                "session": "CLOSED",
                "badge": "🔴 US Market Closed (Weekend)",
                "color": "#EF4444",
                "details": f"Opens Monday 9:30 AM ET (Current: {now_et.strftime('%a %I:%M %p ET')})",
            }
        elif market_open <= current_time < market_close:
            return {
                "session": "REGULAR",
                "badge": "🟢 US Market Live",
                "color": "#10B981",
                "details": f"Closes 4:00 PM ET (Current: {now_et.strftime('%I:%M %p ET')})",
            }
        elif pre_open <= current_time < market_open:
            return {
                "session": "PRE",
                "badge": "🟡 US Pre-Market Session",
                "color": "#F59E0B",
                "details": f"Regular bell 9:30 AM ET (Current: {now_et.strftime('%I:%M %p ET')})",
            }
        elif market_close <= current_time < after_close:
            return {
                "session": "POST",
                "badge": "🌙 US After-Hours Session",
                "color": "#8B5CF6",
                "details": f"After-hours closes 8:00 PM ET (Current: {now_et.strftime('%I:%M %p ET')})",
            }
        else:
            return {
                "session": "CLOSED",
                "badge": "🔴 US Market Closed (Night)",
                "color": "#64748B",
                "details": f"Pre-market opens 4:00 AM ET (Current: {now_et.strftime('%I:%M %p ET')})",
            }


def get_pre_post_market(info: Dict[str, Any], regular_price: float) -> Dict[str, Any]:
    pre_price = info.get("preMarketPrice")
    pre_pct = info.get("preMarketChangePercent")
    pre_change = info.get("preMarketChange")

    if pre_price and not pre_change and regular_price:
        pre_change = pre_price - regular_price
        pre_pct = (pre_change / regular_price) * 100

    post_price = info.get("postMarketPrice")
    post_pct = info.get("postMarketChangePercent")
    post_change = info.get("postMarketChange")

    if post_price and not post_change and regular_price:
        post_change = post_price - regular_price
        post_pct = (post_change / regular_price) * 100

    return {
        "pre_price": pre_price,
        "pre_change": pre_change,
        "pre_pct": pre_pct,
        "post_price": post_price,
        "post_change": post_change,
        "post_pct": post_pct,
    }


def fetch_stock_data(ticker_symbol: str, period: str = "1y") -> Tuple[Optional[pd.DataFrame], Optional[Dict[str, Any]], Optional[str]]:
    clean_symbol = ticker_symbol.strip().upper()
    if not clean_symbol:
        return None, None, "Please enter a valid stock ticker symbol."

    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

        ticker = yf.Ticker(clean_symbol, session=session)
        df = ticker.history(period=period, timeout=10)
        
        if df is None or df.empty:
            return None, None, f"No price data found for '{clean_symbol}'. Yahoo Finance may be rate-limiting or the ticker is invalid."

        df["SMA_20"] = df["Close"].rolling(window=20).mean()
        df["SMA_50"] = df["Close"].rolling(window=50).mean()

        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        df["RSI_14"] = 100 - (100 / (1 + rs))

        info = {}
        try:
            info = ticker.info or {}
        except Exception:
            try:
                fast = ticker.fast_info
                info = {
                    "longName": clean_symbol,
                    "marketCap": getattr(fast, "market_cap", None),
                    "fiftyTwoWeekHigh": getattr(fast, "year_high", None),
                    "fiftyTwoWeekLow": getattr(fast, "year_low", None),
                    "currency": getattr(fast, "currency", "USD"),
                    "exchange": getattr(fast, "exchange", ""),
                }
            except Exception:
                info = {"longName": clean_symbol, "currency": "USD"}

        return df, info, None
    except Exception as e:
        return None, None, f"Failed to load data for '{clean_symbol}': {str(e)}"


def fetch_stock_news(ticker_symbol: str) -> List[Dict[str, Any]]:
    clean_symbol = ticker_symbol.strip().upper()
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        ticker = yf.Ticker(clean_symbol, session=session)
        raw_news = ticker.news or []
        
        parsed_news = []
        for item in raw_news[:6]:
            c = item.get("content", item)
            title = c.get("title") or c.get("headline")
            
            provider = "Financial News"
            if isinstance(c.get("provider"), dict):
                provider = c.get("provider", {}).get("displayName", "Financial News")
            elif c.get("publisher"):
                provider = c.get("publisher")

            link = c.get("canonicalUrl", {}).get("url") if isinstance(c.get("canonicalUrl"), dict) else None
            if not link and isinstance(c.get("clickThroughUrl"), dict):
                link = c.get("clickThroughUrl", {}).get("url")
            if not link:
                link = c.get("link") or c.get("url") or "#"

            pub_date = c.get("pubDate") or c.get("displayTime")
            time_str = "Recent"
            if pub_date:
                try:
                    time_str = pub_date[:16].replace("T", " ") + " UTC"
                except Exception:
                    pass

            if title:
                parsed_news.append({
                    "title": title,
                    "link": link,
                    "publisher": provider,
                    "time": time_str,
                })
        return parsed_news
    except Exception as e:
        print(f"Error fetching news for {clean_symbol}: {e}")
        return []


def analyze_news_sentiment(
    gemini_api_key: Optional[str],
    ticker_symbol: str,
    news_items: List[Dict[str, Any]],
    current_price: float,
    company_name: str,
    currency_symbol: str = "$"
) -> Dict[str, Any]:
    if not news_items:
        return {
            "score": 0,
            "label": "NEUTRAL",
            "color": "#64748B",
            "summary": f"No recent news articles detected for {ticker_symbol}. Neutral sentiment assumed.",
            "takeaways": ["Monitoring for fresh corporate filings and market updates."],
        }

    headlines_text = "\n".join([f"- {item['title']} (Source: {item['publisher']})" for item in news_items])

    if gemini_api_key and gemini_api_key.strip():
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_api_key.strip())
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
You are a senior hedge fund market sentiment analyst.
Analyze the following recent news headlines for {company_name} ({ticker_symbol}), currently trading at {currency_symbol}{current_price:,.2f}.

Headlines:
{headlines_text}

Task:
Evaluate the overall market sentiment from these news items.
Respond ONLY with a JSON object in this exact format:
{{
  "score": <integer from -10 to +10, where -10 is extremely bearish, 0 is neutral, +10 is extremely bullish>,
  "label": "BULLISH" | "SOMEWHAT BULLISH" | "NEUTRAL" | "SOMEWHAT BEARISH" | "BEARISH",
  "summary": "2-3 sentence executive market summary explaining the primary driver of sentiment.",
  "takeaways": [
    "Key takeaway point 1",
    "Key takeaway point 2",
    "Key takeaway point 3"
  ]
}}
"""
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json", "temperature": 0.2}
            )

            result_text = response.text.strip()
            cleaned = result_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)

            score = int(data.get("score", 0))
            color = "#10B981" if score > 2 else ("#EF4444" if score < -2 else "#F59E0B")

            return {
                "score": score,
                "label": data.get("label", "NEUTRAL"),
                "color": color,
                "summary": data.get("summary", "Analysis completed."),
                "takeaways": data.get("takeaways", []),
                "source": "AI-Powered (Google Gemini)",
            }
        except Exception as e:
            print(f"Gemini API call failed: {e}")

    bullish_keywords = ["growth", "soars", "record", "profit", "beats", "upgrade", "buy", "ai", "high", "gain", "surge", "strong", "rally"]
    bearish_keywords = ["falls", "drops", "slumps", "plunge", "loss", "downgrade", "sell", "lawsuit", "investigation", "miss", "weak", "cut"]

    score = 0
    all_text = " ".join([item["title"].lower() for item in news_items])
    for w in bullish_keywords:
        if w in all_text:
            score += 2
    for w in bearish_keywords:
        if w in all_text:
            score -= 2

    score = max(-10, min(10, score))
    label = "BULLISH" if score > 2 else ("BEARISH" if score < -2 else "NEUTRAL")
    color = "#10B981" if score > 2 else ("#EF4444" if score < -2 else "#F59E0B")

    return {
        "score": score,
        "label": label,
        "color": color,
        "summary": f"Automated headline keyword scan indicates a {label.lower()} bias across {len(news_items)} recent news releases.",
        "takeaways": [
            f"Analyzed {len(news_items)} real-time financial articles.",
            "Add a free Gemini API key in the sidebar to unlock neural sentiment reasoning.",
        ],
        "source": "Rule-Based Scanner (Add Gemini Key for AI)",
    }


def get_price_targets(info: Dict[str, Any], current_price: float) -> Dict[str, Any]:
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


def generate_scenarios(info: Dict[str, Any], df: pd.DataFrame, current_price: float, targets: Dict[str, Any], currency_sym: str = "$") -> Dict[str, Any]:
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

    bull_target = targets["high"] if targets["high"] else round(latest_close * 1.25, 2)
    bear_target = targets["low"] if targets["low"] else round(latest_close * 0.80, 2)
    bull_upside = ((bull_target - latest_close) / latest_close) * 100
    bear_downside = ((bear_target - latest_close) / latest_close) * 100

    bull_points = []
    if revenue_growth and revenue_growth > 0:
        bull_points.append(f"Accelerating Revenue Growth: Expanding at {revenue_growth * 100:.1f}% YoY.")
    else:
        bull_points.append("Core market leadership and defensive cash-flow generation.")

    if profit_margin and profit_margin > 0.15:
        bull_points.append(f"High Profitability: Robust net profit margins of {profit_margin * 100:.1f}%.")
    else:
        bull_points.append("Margin expansion potential through operational scale.")

    if latest_close >= sma_50:
        bull_points.append(f"Bullish Trend: Holding firmly above the 50-day moving average ({currency_sym}{sma_50:,.2f}).")
    elif rsi < 35:
        bull_points.append(f"Oversold Bounce: RSI is at {rsi:.1f}, indicating high potential for mean-reversion rally.")
    else:
        bull_points.append(f"Technical momentum testing resistance near 52-week high of {currency_sym}{high_52:,.2f}.")

    if targets["opinions_count"] and targets["opinions_count"] > 5:
        bull_points.append(f"Wall Street / Dalal Street Consensus: Covered by {targets['opinions_count']} analysts with a '{targets['recommendation']}' rating.")

    bear_points = []
    if pe and pe > 40:
        bear_points.append(f"Valuation Risk: Elevated P/E ratio ({pe:.1f}x) leaves little buffer for earnings misses.")
    elif pe:
        bear_points.append(f"Multiple Compression: P/E is {pe:.1f}x, which could compress during risk-off market shifts.")
    else:
        bear_points.append("Vulnerability to earnings multiple contraction.")

    if debt_to_equity and debt_to_equity > 150:
        bear_points.append(f"Leverage Concerns: Elevated Debt-to-Equity ratio of {debt_to_equity:.1f}%.")
    else:
        bear_points.append("Vulnerability to interest rate environment and macro liquidity tightening.")

    if latest_close < sma_50:
        bear_points.append(f"Technical Breakdown: Trading below the critical 50-day moving average ({currency_sym}{sma_50:,.2f}).")
    elif rsi > 70:
        bear_points.append(f"Overbought Territory: RSI is at {rsi:.1f}, signaling elevated risk of short-term pullback.")
    else:
        bear_points.append(f"Downside support test towards 52-week support around {currency_sym}{low_52:,.2f}.")

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
