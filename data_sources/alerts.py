"""Price alerts, earnings calendar, insider trading, position sizing, and signal history."""
import json
import os
from datetime import datetime, timedelta

import requests
import yfinance as yf
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNAL_HISTORY_PATH = os.path.join(BASE_DIR, "signal_history.json")


# ---------------------------------------------------------------------------
# A) Earnings Calendar
# ---------------------------------------------------------------------------

def get_earnings_alerts(portfolio_symbols, lookahead_days=5):
    """Check earnings dates for portfolio stocks; flag those reporting within lookahead_days."""
    alerts = []
    today = datetime.now().date()
    cutoff = today + timedelta(days=lookahead_days)

    for symbol in portfolio_symbols:
        try:
            ticker = yf.Ticker(symbol)
            # yfinance exposes earnings dates via .calendar or .earnings_dates
            cal = ticker.calendar
            if cal is not None:
                # calendar can be a dict or DataFrame depending on yfinance version
                earnings_date = None
                if isinstance(cal, dict):
                    earnings_date = cal.get("Earnings Date")
                    if isinstance(earnings_date, list) and len(earnings_date) > 0:
                        earnings_date = earnings_date[0]
                else:
                    # DataFrame path
                    if hasattr(cal, "columns"):
                        if "Earnings Date" in cal.columns:
                            earnings_date = cal["Earnings Date"].iloc[0]
                        elif len(cal) > 0:
                            earnings_date = cal.index[0]

                if earnings_date is not None:
                    # Normalize to date
                    if hasattr(earnings_date, "date"):
                        ed = earnings_date.date()
                    elif isinstance(earnings_date, str):
                        ed = datetime.strptime(earnings_date[:10], "%Y-%m-%d").date()
                    else:
                        continue

                    if today <= ed <= cutoff:
                        days_until = (ed - today).days
                        alerts.append({
                            "symbol": symbol,
                            "earnings_date": ed.isoformat(),
                            "days_until": days_until,
                            "warning": f"Earnings in {days_until} day{'s' if days_until != 1 else ''}!",
                        })
        except Exception as e:
            print(f"  Earnings check failed for {symbol}: {e}")

    return alerts


# ---------------------------------------------------------------------------
# B) Insider Trading Tracker
# ---------------------------------------------------------------------------

def get_insider_activity(portfolio_symbols, max_per_stock=5):
    """Scrape OpenInsider for recent insider buys/sells for portfolio stocks."""
    results = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    for symbol in portfolio_symbols:
        try:
            url = f"http://openinsider.com/screener?s={symbol}"
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table", class_="tinytable")
            if not table:
                continue

            rows = table.find_all("tr")[1:]  # skip header
            trades = []
            for row in rows[:max_per_stock]:
                cells = row.find_all("td")
                if len(cells) < 12:
                    continue

                filing_date = cells[1].get_text(strip=True)
                trade_date = cells[2].get_text(strip=True)
                insider_name = cells[4].get_text(strip=True)
                title = cells[5].get_text(strip=True)
                trade_type = cells[6].get_text(strip=True)  # P-Purchase, S-Sale
                price = cells[8].get_text(strip=True)
                qty = cells[9].get_text(strip=True)
                value = cells[11].get_text(strip=True)

                # Classify as buy or sell
                is_buy = "P" in trade_type.upper() or "Purchase" in trade_type
                trades.append({
                    "date": trade_date,
                    "insider": insider_name,
                    "title": title,
                    "type": "BUY" if is_buy else "SELL",
                    "price": price,
                    "qty": qty,
                    "value": value,
                })

            if trades:
                results[symbol] = trades

        except Exception as e:
            print(f"  Insider data failed for {symbol}: {e}")

    return results


# ---------------------------------------------------------------------------
# C) Price Alerts
# ---------------------------------------------------------------------------

def get_price_alerts(stock_data, portfolio_symbols):
    """Detect price alerts: 52-week high/low proximity, MA breaks, unusual volume."""
    alerts = []

    for symbol in portfolio_symbols:
        data = stock_data.get(symbol)
        if not data:
            continue

        price = data.get("price", 0)
        high_52w = data.get("high_52w")
        low_52w = data.get("low_52w")
        sma_20 = data.get("sma_20")
        sma_50 = data.get("sma_50")
        volume_ratio = data.get("volume_ratio", 1.0)

        stock_alerts = []

        # Near 52-week high (within 3%)
        if high_52w and price and price > 0:
            pct_from_high = (high_52w - price) / price * 100
            if pct_from_high <= 3:
                stock_alerts.append({
                    "type": "52W_HIGH",
                    "message": f"Near 52-week high (${high_52w:.2f}, current ${price:.2f})",
                    "severity": "info",
                })

        # Near 52-week low (within 5%)
        if low_52w and price and price > 0:
            pct_from_low = (price - low_52w) / low_52w * 100
            if pct_from_low <= 5:
                stock_alerts.append({
                    "type": "52W_LOW",
                    "message": f"Near 52-week low (${low_52w:.2f}, current ${price:.2f})",
                    "severity": "warning",
                })

        # Breaking above 20-day SMA
        if sma_20 and price:
            if price > sma_20 and (price - sma_20) / sma_20 * 100 < 1.5:
                stock_alerts.append({
                    "type": "ABOVE_SMA20",
                    "message": f"Just broke above 20-day SMA (${sma_20:.2f})",
                    "severity": "bullish",
                })
            elif price < sma_20 and (sma_20 - price) / price * 100 < 1.5:
                stock_alerts.append({
                    "type": "BELOW_SMA20",
                    "message": f"Just broke below 20-day SMA (${sma_20:.2f})",
                    "severity": "bearish",
                })

        # Breaking above/below 50-day SMA
        if sma_50 and price:
            if price > sma_50 and (price - sma_50) / sma_50 * 100 < 2:
                stock_alerts.append({
                    "type": "ABOVE_SMA50",
                    "message": f"Breaking above 50-day SMA (${sma_50:.2f})",
                    "severity": "bullish",
                })
            elif price < sma_50 and (sma_50 - price) / price * 100 < 2:
                stock_alerts.append({
                    "type": "BELOW_SMA50",
                    "message": f"Breaking below 50-day SMA (${sma_50:.2f})",
                    "severity": "bearish",
                })

        # Unusual volume (>2x average)
        if volume_ratio >= 2.0:
            stock_alerts.append({
                "type": "VOLUME_SPIKE",
                "message": f"Unusual volume ({volume_ratio:.1f}x average)",
                "severity": "alert",
            })

        if stock_alerts:
            alerts.append({
                "symbol": symbol,
                "price": price,
                "alerts": stock_alerts,
            })

    return alerts


# ---------------------------------------------------------------------------
# D) Position Sizing
# ---------------------------------------------------------------------------

def calculate_position_sizes(portfolio_holdings, stock_data, opportunities, max_position_pct=0.10):
    """
    Suggest dollar amounts for new positions based on total portfolio value and conviction score.
    max_position_pct: maximum percentage of portfolio for a single new position (default 10%).
    """
    # Calculate total portfolio value
    total_value = 0.0
    for holding in portfolio_holdings:
        symbol = holding.get("symbol")
        shares = holding.get("shares", 0)
        data = stock_data.get(symbol)
        if data and data.get("price"):
            total_value += data["price"] * shares

    if total_value <= 0:
        return {"total_portfolio_value": 0, "suggestions": []}

    suggestions = []
    for opp in opportunities:
        score = opp.get("total_score", 0)
        # Map score to conviction level and allocation percentage
        if score >= 40:
            conviction = "HIGH"
            alloc_pct = max_position_pct  # Full 10%
        elif score >= 25:
            conviction = "MEDIUM-HIGH"
            alloc_pct = max_position_pct * 0.7  # 7%
        elif score >= 15:
            conviction = "MEDIUM"
            alloc_pct = max_position_pct * 0.5  # 5%
        else:
            conviction = "LOW"
            alloc_pct = max_position_pct * 0.3  # 3%

        suggested_amount = total_value * alloc_pct
        price = opp.get("price", 0)
        suggested_shares = int(suggested_amount / price) if price > 0 else 0

        suggestions.append({
            "symbol": opp["symbol"],
            "name": opp.get("name", opp["symbol"]),
            "score": score,
            "conviction": conviction,
            "suggested_amount": round(suggested_amount, 2),
            "suggested_shares": suggested_shares,
            "price": price,
        })

    return {
        "total_portfolio_value": round(total_value, 2),
        "suggestions": suggestions,
    }


# ---------------------------------------------------------------------------
# E) Historical Accuracy / Signal History
# ---------------------------------------------------------------------------

def load_signal_history():
    """Load past signal history from JSON file."""
    if os.path.exists(SIGNAL_HISTORY_PATH):
        try:
            with open(SIGNAL_HISTORY_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"signals": [], "accuracy_stats": {}}
    return {"signals": [], "accuracy_stats": {}}


def save_signal_history(history):
    """Save signal history to JSON file."""
    with open(SIGNAL_HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2, default=str)


def log_signals(scored_stocks):
    """Log today's signals for future accuracy checking."""
    history = load_signal_history()
    today = datetime.now().date().isoformat()

    # Avoid duplicate logging for the same day
    existing_dates = {s.get("date") for s in history["signals"]}
    if today in existing_dates:
        return history

    for stock in scored_stocks:
        if stock.get("total_score", 0) >= 20 or stock.get("total_score", 0) <= -20:
            history["signals"].append({
                "date": today,
                "symbol": stock["symbol"],
                "price_at_signal": stock.get("price", 0),
                "score": stock.get("total_score", 0),
                "rating": stock.get("rating", ""),
                "checked": False,
                "outcome": None,
            })

    save_signal_history(history)
    return history


def check_signal_accuracy():
    """Check signals from 7+ days ago to see if the predicted direction was correct."""
    history = load_signal_history()
    cutoff = (datetime.now() - timedelta(days=7)).date().isoformat()
    updated = False

    for signal in history["signals"]:
        if signal.get("checked"):
            continue
        if signal["date"] > cutoff:
            continue  # Not yet 7 days old

        # Fetch current price
        try:
            ticker = yf.Ticker(signal["symbol"])
            hist = ticker.history(period="1d")
            if hist.empty:
                continue
            current_price = hist.iloc[-1]["Close"]
            signal_price = signal.get("price_at_signal", 0)

            if signal_price <= 0:
                continue

            price_change_pct = (current_price - signal_price) / signal_price * 100

            # A bullish signal (score >= 20) is correct if price went up
            # A bearish signal (score <= -20) is correct if price went down
            was_bullish = signal.get("score", 0) >= 20
            if was_bullish:
                correct = price_change_pct > 0
            else:
                correct = price_change_pct < 0

            signal["checked"] = True
            signal["outcome"] = {
                "current_price": round(current_price, 2),
                "price_change_pct": round(price_change_pct, 2),
                "correct": correct,
            }
            updated = True
        except Exception:
            pass

    if updated:
        # Update accuracy stats
        checked_signals = [s for s in history["signals"] if s.get("checked")]
        correct_count = sum(1 for s in checked_signals if s.get("outcome", {}).get("correct"))
        total_checked = len(checked_signals)
        history["accuracy_stats"] = {
            "total_signals": len(history["signals"]),
            "checked": total_checked,
            "correct": correct_count,
            "accuracy_pct": round(correct_count / total_checked * 100, 1) if total_checked > 0 else 0,
            "last_updated": datetime.now().isoformat(),
        }
        save_signal_history(history)

    return history.get("accuracy_stats", {})
