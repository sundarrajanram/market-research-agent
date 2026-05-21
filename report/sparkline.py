"""Generate Gmail-compatible inline sparkline from price data."""
import yfinance as yf
from data_sources.portfolio_loader import load_portfolio


def generate_portfolio_sparkline(width=180, height=40):
    """Generate a 30-day portfolio value sparkline as Gmail-compatible HTML table."""
    portfolio = load_portfolio()
    if not portfolio:
        return ""

    daily_values = None

    for holding in portfolio:
        symbol = holding["symbol"]
        shares = holding.get("shares", 0)
        if shares <= 0:
            continue

        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")
            if hist.empty or len(hist) < 5:
                continue

            stock_value = hist["Close"] * shares

            if daily_values is None:
                daily_values = stock_value.copy()
            else:
                common = daily_values.index.intersection(stock_value.index)
                if len(common) > 0:
                    daily_values = daily_values.reindex(common) + stock_value.reindex(common)
        except Exception:
            continue

    if daily_values is None or len(daily_values) < 5:
        return ""

    values = daily_values.values.tolist()
    min_val = min(values)
    max_val = max(values)
    val_range = max_val - min_val if max_val != min_val else 1

    # Determine color
    trend_pct = ((values[-1] - values[0]) / values[0]) * 100
    bar_color = "#34d399" if trend_pct >= 0 else "#f87171"

    # Sample down to ~20 bars for clean display
    num_bars = 20
    step = max(1, len(values) // num_bars)
    sampled = values[::step][-num_bars:]

    # Normalize bar heights (4px to height px)
    bar_heights = []
    for val in sampled:
        pct = (val - min_val) / val_range
        h = max(4, int(pct * height))
        bar_heights.append(h)

    # Format portfolio value
    current_val = values[-1]
    if current_val >= 1000000:
        val_display = f"${current_val/1000000:.2f}M"
    elif current_val >= 1000:
        val_display = f"${current_val/1000:.1f}K"
    else:
        val_display = f"${current_val:.0f}"

    trend_display = f"{'+'if trend_pct >= 0 else ''}{trend_pct:.1f}%"
    trend_color = "#34d399" if trend_pct >= 0 else "#f87171"

    # Build HTML table-based bar chart (works in Gmail)
    bar_width = max(4, width // num_bars - 2)
    bars_html = ""
    for h in bar_heights:
        bars_html += (
            f'<td style="vertical-align: bottom; padding: 0 1px;">'
            f'<div style="width: {bar_width}px; height: {h}px; background: {bar_color}; border-radius: 2px 2px 0 0;"></div>'
            f'</td>'
        )

    html = f"""<table cellpadding="0" cellspacing="0" border="0" style="display: inline-block;">
    <tr>{bars_html}</tr>
</table>
<div style="font-size: 11px; margin-top: 4px; text-align: center;">
    <span style="color: #e2e8f0; font-weight: 600;">{val_display}</span>
    <span style="color: {trend_color}; font-weight: 600; margin-left: 4px;">{trend_display}</span>
    <span style="color: #64748b; margin-left: 4px;">30d</span>
</div>"""

    return html
