"""Market Open Report - Short, punchy email sent at 7 AM PST."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
import yfinance as yf
from jinja2 import Template

from data_sources.portfolio_loader import load_portfolio
from data_sources.heatmap import generate_heatmap_html
from email_sender import send_market_open_report
import config


def get_premarket_data(symbols):
    """Fetch pre-market/early session data for portfolio stocks."""
    movers = []
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            # Get current price and previous close for gap detection
            current_price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
            prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose", 0)
            pre_market_price = info.get("preMarketPrice")
            pre_market_change_pct = info.get("preMarketChangePercent")

            # Use pre-market price if available, otherwise regular market
            if pre_market_price and prev_close:
                change_pct = (pre_market_price - prev_close) / prev_close * 100
                price_used = pre_market_price
                is_premarket = True
            elif current_price and prev_close and prev_close > 0:
                change_pct = (current_price - prev_close) / prev_close * 100
                price_used = current_price
                is_premarket = False
            else:
                continue

            # Classify the gap
            gap_type = None
            if change_pct >= 2:
                gap_type = "GAP_UP"
            elif change_pct <= -2:
                gap_type = "GAP_DOWN"

            movers.append({
                "symbol": symbol,
                "name": info.get("shortName", symbol),
                "price": round(price_used, 2),
                "prev_close": round(prev_close, 2),
                "change_pct": round(change_pct, 2),
                "gap_type": gap_type,
                "is_premarket": is_premarket,
                "volume": info.get("volume", 0) or 0,
                "avg_volume": info.get("averageVolume", 0) or 0,
            })
        except Exception as e:
            print(f"  Pre-market fetch failed for {symbol}: {e}")

    # Sort by absolute change percentage (biggest movers first)
    movers.sort(key=lambda x: abs(x["change_pct"]), reverse=True)
    return movers


def get_market_trend():
    """Get first 30-min trend direction from index futures/ETFs."""
    trend_data = {}
    futures = {
        "SPY": "S&P 500",
        "QQQ": "NASDAQ",
        "DIA": "Dow Jones",
    }

    for etf, name in futures.items():
        try:
            ticker = yf.Ticker(etf)
            info = ticker.info
            current = info.get("currentPrice") or info.get("regularMarketPrice", 0)
            prev_close = info.get("previousClose", 0)
            if current and prev_close and prev_close > 0:
                change_pct = (current - prev_close) / prev_close * 100
                if change_pct >= 0.3:
                    direction = "UP"
                elif change_pct <= -0.3:
                    direction = "DOWN"
                else:
                    direction = "FLAT"
                trend_data[name] = {
                    "price": round(current, 2),
                    "change_pct": round(change_pct, 2),
                    "direction": direction,
                }
        except Exception as e:
            print(f"  Trend fetch failed for {etf}: {e}")

    return trend_data


def generate_action_items(movers):
    """Generate quick action items based on pre-market activity."""
    items = []
    for m in movers:
        symbol = m["symbol"]
        change = m["change_pct"]
        name = m["name"]

        if m["gap_type"] == "GAP_DOWN" and change <= -3:
            items.append(f"{symbol} gapped down {abs(change):.1f}% -- consider buying dip if thesis intact")
        elif m["gap_type"] == "GAP_DOWN":
            items.append(f"{symbol} down {abs(change):.1f}% pre-market -- watch for support at open")
        elif m["gap_type"] == "GAP_UP" and change >= 3:
            items.append(f"{symbol} up {change:.1f}% pre-market -- don't chase; wait for pullback")
        elif m["gap_type"] == "GAP_UP":
            items.append(f"{symbol} up {change:.1f}% -- strength continues, hold position")

        # Volume-based action
        if m["avg_volume"] and m["volume"] > m["avg_volume"] * 2:
            items.append(f"{symbol} showing 2x+ volume -- institutional interest likely")

    return items[:6]  # Keep it concise


MARKET_OPEN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif; background: #0a0e17; color: #e2e8f0; padding: 16px; line-height: 1.5; }
    .container { max-width: 600px; margin: 0 auto; }

    .header { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border: 1px solid #f59e0b; border-radius: 10px; padding: 20px; margin-bottom: 12px; position: relative; overflow: hidden; }
    .header::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #f59e0b, #ef4444, #f59e0b); }
    .header h1 { font-size: 18px; font-weight: 700; color: #fbbf24; }
    .header .date { font-size: 12px; color: #94a3b8; margin-top: 4px; }

    .card { background: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 16px; margin-bottom: 10px; }
    .card h2 { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #64748b; margin-bottom: 10px; }

    .trend-row { display: flex; gap: 12px; margin-bottom: 8px; }
    .trend-box { flex: 1; background: #0f172a; border: 1px solid #1f2937; border-radius: 6px; padding: 10px; text-align: center; }
    .trend-label { font-size: 10px; color: #64748b; text-transform: uppercase; }
    .trend-value { font-size: 16px; font-weight: 700; margin-top: 2px; }
    .trend-dir { font-size: 11px; font-weight: 600; margin-top: 2px; }

    .mover-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #1f2937; }
    .mover-row:last-child { border-bottom: none; }
    .mover-symbol { font-weight: 700; font-size: 14px; color: #f1f5f9; }
    .mover-name { font-size: 11px; color: #64748b; }
    .mover-change { font-size: 14px; font-weight: 700; }
    .gap-badge { display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 9px; font-weight: 700; text-transform: uppercase; margin-left: 6px; }
    .gap-up { background: #064e3b; color: #6ee7b7; }
    .gap-down { background: #7f1d1d; color: #fecaca; }

    .positive { color: #34d399; }
    .negative { color: #f87171; }
    .flat { color: #94a3b8; }

    .action-item { padding: 6px 0; font-size: 13px; color: #cbd5e1; border-bottom: 1px solid #1f2937; }
    .action-item:last-child { border-bottom: none; }
    .action-item::before { content: ''; display: inline-block; width: 6px; height: 6px; background: #f59e0b; border-radius: 50%; margin-right: 8px; }

    .footer { text-align: center; padding: 12px; font-size: 10px; color: #4b5563; }
</style>
</head>
<body>
<div class="container">

<div class="header">
    <h1>Market Open Flash</h1>
    <div class="date">{{ date }} &bull; {{ generated_at }} PST</div>
</div>

{% if trend %}
<div class="card">
    <h2>Market Direction</h2>
    <div class="trend-row">
        {% for name, data in trend.items() %}
        <div class="trend-box">
            <div class="trend-label">{{ name }}</div>
            <div class="trend-value {{ 'positive' if data.change_pct >= 0 else 'negative' }}">
                {{ "+" if data.change_pct >= 0 }}{{ data.change_pct }}%
            </div>
            <div class="trend-dir {{ 'positive' if data.direction == 'UP' else ('negative' if data.direction == 'DOWN' else 'flat') }}">
                {% if data.direction == 'UP' %}Bullish{% elif data.direction == 'DOWN' %}Bearish{% else %}Flat{% endif %}
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endif %}

{% if heatmap_html %}
{{ heatmap_html|safe }}
{% endif %}

{% if movers %}
<div class="card">
    <h2>Your Portfolio - Pre-Market Movers</h2>
    {% for m in movers %}
    <div class="mover-row">
        <div>
            <span class="mover-symbol">{{ m.symbol }}</span>
            <span class="mover-name">{{ m.name }}</span>
            {% if m.gap_type == "GAP_UP" %}<span class="gap-badge gap-up">Gap Up</span>{% endif %}
            {% if m.gap_type == "GAP_DOWN" %}<span class="gap-badge gap-down">Gap Down</span>{% endif %}
        </div>
        <div>
            <span class="mover-change {{ 'positive' if m.change_pct >= 0 else 'negative' }}">
                {{ "+" if m.change_pct >= 0 }}{{ m.change_pct }}%
            </span>
            <div style="font-size: 11px; color: #64748b;">${{ m.price }}</div>
        </div>
    </div>
    {% endfor %}
</div>
{% endif %}

{% if action_items %}
<div class="card">
    <h2>Quick Actions</h2>
    {% for item in action_items %}
    <div class="action-item">{{ item }}</div>
    {% endfor %}
</div>
{% endif %}

<div class="footer">
    <p>Quick glance only. Not financial advice. DYOR.</p>
</div>

</div>
</body>
</html>
"""


def generate_market_open_report():
    """Generate and send the market open flash report."""
    print(f"[{datetime.now()}] Starting Market Open report...")

    # Load portfolio symbols
    portfolio = load_portfolio()
    portfolio_symbols = [h["symbol"] for h in portfolio if h.get("symbol")]

    if not portfolio_symbols:
        print("  No portfolio symbols found. Skipping market open report.")
        return

    # Fetch pre-market data
    print("  Fetching pre-market data...")
    movers = get_premarket_data(portfolio_symbols)

    # Get market trend
    print("  Fetching market trend...")
    trend = get_market_trend()

    # Generate action items
    action_items = generate_action_items(movers)

    # Build heatmap data using portfolio shares and pre-market prices
    shares_map = {h["symbol"]: h.get("shares", 0) for h in portfolio}
    heatmap_positions = []
    for m in movers:
        shares = shares_map.get(m["symbol"], 0)
        position_value = m["price"] * shares if shares else 0
        heatmap_positions.append({
            "symbol": m["symbol"],
            "position_value": position_value,
            "change_pct": m["change_pct"],
        })
    total_value = sum(p["position_value"] for p in heatmap_positions)
    for p in heatmap_positions:
        p["allocation_pct"] = round((p["position_value"] / total_value) * 100, 1) if total_value > 0 else 0
    heatmap_html = generate_heatmap_html(heatmap_positions)

    # Render HTML
    print("  Generating report...")
    template = Template(MARKET_OPEN_TEMPLATE)
    html = template.render(
        date=datetime.now().strftime("%B %d, %Y"),
        generated_at=datetime.now().strftime("%I:%M %p"),
        trend=trend,
        movers=movers,
        action_items=action_items,
        heatmap_html=heatmap_html,
    )

    # Send
    print("  Sending market open report...")
    send_market_open_report(html)

    print(f"[{datetime.now()}] Market Open report complete!")
    return {
        "movers": movers,
        "trend": trend,
        "action_items": action_items,
    }


if __name__ == "__main__":
    generate_market_open_report()
