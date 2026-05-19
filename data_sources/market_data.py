"""Fetch market data from Yahoo Finance."""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def get_stock_data(symbols, period="1mo"):
    """Get price/volume data for a list of symbols."""
    results = {}
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            if hist.empty:
                continue
            info = ticker.info
            latest = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) > 1 else latest

            results[symbol] = {
                "price": round(latest["Close"], 2),
                "change_pct": round((latest["Close"] - prev["Close"]) / prev["Close"] * 100, 2),
                "volume": int(latest["Volume"]),
                "avg_volume": int(hist["Volume"].mean()),
                "volume_ratio": round(latest["Volume"] / hist["Volume"].mean(), 2),
                "high_52w": round(hist["High"].max(), 2),
                "low_52w": round(hist["Low"].min(), 2),
                "sma_20": round(hist["Close"].tail(20).mean(), 2) if len(hist) >= 20 else None,
                "sma_50": round(hist["Close"].tail(50).mean(), 2) if len(hist) >= 50 else None,
                "rsi": calculate_rsi(hist["Close"]),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "market_cap": info.get("marketCap"),
                "sector": info.get("sector", "Unknown"),
                "name": info.get("shortName", symbol),
            }
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
    return results


def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index."""
    if len(prices) < period + 1:
        return None
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi.iloc[-1], 1)


def get_index_performance(indices):
    """Get performance of major market indices."""
    results = {}
    for idx in indices:
        try:
            ticker = yf.Ticker(idx)
            hist = ticker.history(period="5d")
            if len(hist) >= 2:
                latest = hist.iloc[-1]["Close"]
                prev = hist.iloc[-2]["Close"]
                results[idx] = {
                    "price": round(latest, 2),
                    "change_pct": round((latest - prev) / prev * 100, 2),
                }
        except Exception as e:
            print(f"Error fetching index {idx}: {e}")
    return results


def get_sector_performance(sector_etfs):
    """Get sector ETF performance."""
    results = {}
    for sector, etf in sector_etfs.items():
        try:
            ticker = yf.Ticker(etf)
            hist = ticker.history(period="5d")
            if len(hist) >= 2:
                latest = hist.iloc[-1]["Close"]
                prev = hist.iloc[-2]["Close"]
                week_ago = hist.iloc[0]["Close"]
                results[sector] = {
                    "etf": etf,
                    "price": round(latest, 2),
                    "daily_change": round((latest - prev) / prev * 100, 2),
                    "weekly_change": round((latest - week_ago) / week_ago * 100, 2),
                }
        except Exception as e:
            print(f"Error fetching sector {sector}: {e}")
    return results


def get_earnings_calendar():
    """Get upcoming earnings for watchlist stocks."""
    upcoming = []
    today = datetime.now()
    next_week = today + timedelta(days=7)

    for symbol in ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]:
        try:
            ticker = yf.Ticker(symbol)
            cal = ticker.calendar
            if cal is not None and not cal.empty:
                upcoming.append({"symbol": symbol, "calendar": cal})
        except Exception:
            pass
    return upcoming
