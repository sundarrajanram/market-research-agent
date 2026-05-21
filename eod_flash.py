"""End-of-Day Portfolio Flash — quick P&L summary after market close."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
import yfinance as yf
from data_sources.portfolio_loader import load_portfolio
from email_sender import send_eod_report
import config


def run_eod_flash():
    """Generate and send EOD portfolio flash."""
    print(f"[{datetime.now()}] Starting EOD Flash report...")

    portfolio = load_portfolio()
    if not portfolio:
        print("  No portfolio found.")
        return

    print("  Fetching closing prices...")
    holdings_data = []
    total_day_gain = 0
    total_value = 0

    for holding in portfolio:
        symbol = holding["symbol"]
        shares = holding.get("shares", 0)
        if shares <= 0:
            continue

        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if len(hist) < 2:
                continue

            today_close = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2]
            change_pct = ((today_close - prev_close) / prev_close) * 100
            day_gain = (today_close - prev_close) * shares
            position_value = today_close * shares

            total_day_gain += day_gain
            total_value += position_value

            holdings_data.append({
                "symbol": symbol,
                "price": round(today_close, 2),
                "change_pct": round(change_pct, 2),
                "day_gain": round(day_gain, 2),
                "position_value": round(position_value, 2),
                "shares": shares,
            })
        except Exception as e:
            print(f"    Error fetching {symbol}: {e}")

    # Sort by absolute gain (biggest movers first)
    holdings_data.sort(key=lambda x: abs(x["day_gain"]), reverse=True)

    # Get index performance
    print("  Fetching index data...")
    indices = {}
    for idx, name in [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ"), ("^DJI", "Dow")]:
        try:
            t = yf.Ticker(idx)
            h = t.history(period="5d")
            if len(h) >= 2:
                change = ((h["Close"].iloc[-1] - h["Close"].iloc[-2]) / h["Close"].iloc[-2]) * 100
                indices[name] = round(change, 2)
        except Exception:
            pass

    # Generate HTML
    print("  Generating EOD flash...")
    html = generate_eod_html(holdings_data, total_day_gain, total_value, indices)

    print("  Sending...")
    send_eod_report(html)

    print(f"[{datetime.now()}] EOD Flash complete!")


def generate_eod_html(holdings, total_day_gain, total_value, indices):
    """Generate the EOD flash HTML email — percentages only, no dollar values or share counts."""
    total_pct = (total_day_gain / (total_value - total_day_gain)) * 100 if total_value > total_day_gain else 0
    trend_color = "#34d399" if total_pct >= 0 else "#f87171"
    total_sign = "+" if total_pct >= 0 else ""

    # Winners and losers
    winners = [h for h in holdings if h["change_pct"] > 0]
    losers = [h for h in holdings if h["change_pct"] < 0]
    flat = [h for h in holdings if h["change_pct"] == 0]

    # Index bar
    index_html = ""
    for name, change in indices.items():
        color = "#34d399" if change >= 0 else "#f87171"
        index_html += f'<span style="margin-right: 16px;"><span style="color: #94a3b8;">{name}</span> <span style="color: {color}; font-weight: 600;">{"+" if change >= 0 else ""}{change}%</span></span>'

    # Holdings rows — only ticker, price, and % change
    rows_html = ""
    for h in holdings:
        color = "#34d399" if h["change_pct"] >= 0 else "#f87171"
        rows_html += f"""<tr>
            <td style="padding: 8px 10px; border-bottom: 1px solid #1f2937;">
                <strong style="color: #f1f5f9;">{h['symbol']}</strong>
            </td>
            <td style="padding: 8px 10px; border-bottom: 1px solid #1f2937; text-align: right; color: #cbd5e1;">${h['price']}</td>
            <td style="padding: 8px 10px; border-bottom: 1px solid #1f2937; text-align: right; color: {color}; font-weight: 600;">{"+" if h['change_pct'] >= 0 else ""}{h['change_pct']}%</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif; background: #0a0e17; color: #e2e8f0; padding: 20px; margin: 0;">
<div style="max-width: 600px; margin: 0 auto;">

<div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border: 1px solid #1e40af; border-radius: 12px; padding: 24px; margin-bottom: 16px; position: relative; overflow: hidden;">
    <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #3b82f6, #8b5cf6, #06b6d4);"></div>
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="font-size: 20px; font-weight: 700; color: #f8fafc; margin: 0;">EOD Portfolio Flash</h1>
            <div style="font-size: 12px; color: #64748b; margin-top: 4px;">{datetime.now().strftime('%B %d, %Y')} &bull; Market Close</div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 28px; font-weight: 700; color: {trend_color};">{total_sign}{total_pct:.2f}%</div>
            <div style="font-size: 12px; color: #64748b;">portfolio today</div>
        </div>
    </div>
</div>

<div style="background: #111827; border: 1px solid #1f2937; border-radius: 10px; padding: 16px; margin-bottom: 12px;">
    <div style="font-size: 12px;">{index_html}</div>
</div>

<div style="background: #111827; border: 1px solid #1f2937; border-radius: 10px; padding: 16px; margin-bottom: 12px;">
    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
        <tr>
            <th style="text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; padding: 8px 10px; border-bottom: 1px solid #1f2937;">Stock</th>
            <th style="text-align: right; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; padding: 8px 10px; border-bottom: 1px solid #1f2937;">Price</th>
            <th style="text-align: right; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; padding: 8px 10px; border-bottom: 1px solid #1f2937;">Change</th>
        </tr>
        {rows_html}
    </table>
</div>

<div style="background: #111827; border: 1px solid #1f2937; border-radius: 10px; padding: 16px; margin-bottom: 12px;">
    <div style="display: flex; gap: 24px;">
        <div>
            <div style="font-size: 10px; color: #64748b; text-transform: uppercase;">Winners</div>
            <div style="font-size: 20px; font-weight: 700; color: #34d399;">{len(winners)}</div>
        </div>
        <div>
            <div style="font-size: 10px; color: #64748b; text-transform: uppercase;">Losers</div>
            <div style="font-size: 20px; font-weight: 700; color: #f87171;">{len(losers)}</div>
        </div>
        <div>
            <div style="font-size: 10px; color: #64748b; text-transform: uppercase;">Flat</div>
            <div style="font-size: 20px; font-weight: 700; color: #94a3b8;">{len(flat)}</div>
        </div>
    </div>
</div>

<div style="text-align: center; padding: 16px; font-size: 11px; color: #4b5563;">
    <p>EOD Flash &bull; {datetime.now().strftime('%I:%M %p')} PST &bull; Market Intelligence Agent</p>
</div>

</div>
</body>
</html>"""

    return html


if __name__ == "__main__":
    run_eod_flash()
