# Trading Simulation

A Python-based trading simulator using SET50 daily tick data.  
This system mimics real-time trading environments and supports development of algorithmic (ALGO) trading strategies with features such as order matching, portfolio management, commission/VAT handling, and more.

---

## 💼 Overview

The simulator reproduces a streaming-like stock trading system with capabilities including:

- Order placement and matching
- Real-time-like data streaming
- Portfolio tracking and analysis
- Automated performance summarization

Each trader starts with an **initial cash balance of 10,000,000 THB**. This capital will be managed through the portfolio system and used throughout the trading competition or simulation.

---

## 🧠 Features

### 📈 Stock & Portfolio Management

- Initialize a portfolio or load an existing one
- Update market prices during simulation
- Track and calculate key financial metrics:
  - Amount by cost
  - Average cost per stock
  - Unrealized & realized gains/losses (in value and %)
  - Net Asset Value (NAV)
  - Maximum Drawdown
  - Calmar Ratio

### 📊 Portfolio Summary

- Automatically generate transaction summaries
- Output metrics such as buy/sell volume, average price, commission, VAT, and net result

### 📝 Order Handling

- Submit buy/sell orders under these rules:
  - Stocks must belong to the **SET50 index**
  - Volume must be a multiple of 100 (standard lot size)
  - Partial or invalid volumes (e.g. 150) are rejected
  - Orders exceeding portfolio cash will be rejected
- All valid orders are recorded and matched against streaming market data

### 🔁 Order Matching Simulation

- Market simulator checks all orders during each time step
- Orders are executed only if matched price/volume is available in the stream
- Realistic handling of slippage, VAT (7%), and commission (0.157%), and slippage (0.03%)

### 📤 Strategy Result Submission

- After simulation, trading performance and results are automatically generated
- Ensure the portfolio name matches your trader/team name for correct result assignment

---

## ⚙️ Requirements

- Python 3.9.13+
- pandas
- rich
- gspread
- google-auth
- google-api-python-client
- google-auth-httplib2
- google-auth-oauthlib

Install dependencies:

```bash
pip install -r requirements.txt
