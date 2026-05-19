# Daily Market Research Agent

Automated market research tool that analyzes stocks daily and emails investment suggestions before market open.

## Features

- **Market Data**: Real-time prices, volume, technical indicators (RSI, SMA, momentum)
- **Technical Analysis**: Automated scoring with buy/sell signals
- **Fundamental Analysis**: P/E ratios, earnings growth expectations
- **News Aggregation**: Reuters, Yahoo Finance, MarketWatch, CNBC
- **Sentiment Analysis**: CNN Fear & Greed Index, Reddit trending tickers
- **Motley Fool**: Premium recommendations from your subscription
- **Sector Analysis**: ETF-based sector rotation insights
- **Beautiful HTML Reports**: Professional email format with color-coded signals

## Setup

```bash
chmod +x setup.sh
./setup.sh
```

## Gmail App Password Setup

Since you need to send emails, create a Gmail App Password:

1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification (required first)
3. Go to https://myaccount.google.com/apppasswords
4. Select "Mail" and "Other (Custom name)"
5. Name it "Market Research Agent"
6. Copy the 16-character password
7. Paste it in `.env` as `SMTP_PASSWORD`

## Usage

### One-time test run:
```bash
source venv/bin/activate
python main.py
```

### Run scheduler (stays running, triggers at 5 AM PST):
```bash
source venv/bin/activate
python scheduler.py
```

### Run as cron job (alternative to scheduler):
```cron
0 5 * * 1-5 cd /path/to/market-research-agent && venv/bin/python main.py
```

## Customization

Edit `config.py` to:
- Change the stock watchlist
- Add/remove market indices
- Modify sector ETFs

## Project Structure

```
market-research-agent/
├── main.py              # Entry point - orchestrates the pipeline
├── scheduler.py         # Daily scheduler (5 AM PST)
├── config.py            # Configuration and watchlist
├── email_sender.py      # Email delivery
├── data_sources/
│   ├── market_data.py   # Yahoo Finance data
│   ├── news_sentiment.py # News, Fear/Greed, Reddit
│   └── motley_fool.py   # Motley Fool scraper
├── analysis/
│   ├── technical.py     # Technical indicator scoring
│   └── fundamental.py   # Fundamental analysis
├── report/
│   └── generator.py     # HTML report template
├── .env                 # Your credentials (not in git)
└── reports/             # Saved HTML reports
```
