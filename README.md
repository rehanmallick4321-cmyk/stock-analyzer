# 📈 Interactive Stock Analyzer & Bull/Bear Scenario Engine

A modern financial dashboard built with **Python**, **Streamlit**, **yfinance**, and **Plotly**. Designed for clear, visual equity research without needing paid API keys or financial subscriptions.

---

## 🌟 Key Features

1. **Wall Street Price Targets**:
   - Shows analyst Consensus Rating (Buy / Hold / Sell).
   - Displays Target Low, Target Mean, and Target High with upside/downside percentages.
   - Interactive horizontal spread visualization comparing the current price to analyst ranges.

2. **⚖️ Dynamic Bull vs. Bear Scenarios**:
   - **🟢 Bull Case**: Calculates upside potential based on peak analyst targets, revenue growth acceleration, healthy net profit margins, and moving average support.
   - **🔴 Bear Case**: Evaluates downside risks, multiple compression vulnerabilities (high P/E), leverage/debt-to-equity ratios, and technical breakdown levels.

3. **📊 Interactive Technical Charts**:
   - Toggle between **Candlestick** and **Line** charts.
   - 20-Day and 50-Day Simple Moving Averages (SMA).
   - Interactive volume histogram.
   - Zoom, pan, and hover over historical price action.

4. **100% Free & No Setup**:
   - Powered by `yfinance` — zero API keys or credit cards required.

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
Open your terminal or command prompt and run:
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
Run the Streamlit app:
```bash
streamlit run app.py
```

It will automatically launch in your browser at `http://localhost:8501`.

---

## 📁 Project Structure

```text
stock-analyzer/
├── app.py              # Streamlit dashboard interface & interactive Plotly charts
├── analysis.py         # Financial data retrieval, technical indicators, and Bull/Bear logic
├── requirements.txt    # Python library dependencies
└── README.md           # Documentation and setup instructions
```
