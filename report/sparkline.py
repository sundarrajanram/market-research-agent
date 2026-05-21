"""Generate inline SVG sparklines from price data."""
import yfinance as yf
from data_sources.portfolio_loader import load_portfolio


def generate_portfolio_sparkline(width=200, height=50):
    """Generate a 30-day portfolio value sparkline as inline SVG."""
    portfolio = load_portfolio()
    if not portfolio:
        return ""

    # Get 30-day history for each holding
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
                # Align dates and add
                common = daily_values.index.intersection(stock_value.index)
                if len(common) > 0:
                    daily_values = daily_values.reindex(common) + stock_value.reindex(common)
        except Exception:
            continue

    if daily_values is None or len(daily_values) < 5:
        return ""

    # Normalize to SVG coordinates
    values = daily_values.values.tolist()
    min_val = min(values)
    max_val = max(values)
    val_range = max_val - min_val if max_val != min_val else 1

    padding = 4
    chart_width = width - (padding * 2)
    chart_height = height - (padding * 2)

    points = []
    for i, val in enumerate(values):
        x = padding + (i / (len(values) - 1)) * chart_width
        y = padding + chart_height - ((val - min_val) / val_range) * chart_height
        points.append(f"{x:.1f},{y:.1f}")

    polyline_points = " ".join(points)

    # Determine color based on trend
    trend_pct = ((values[-1] - values[0]) / values[0]) * 100
    if trend_pct >= 0:
        line_color = "#34d399"
        fill_color = "#34d39920"
    else:
        line_color = "#f87171"
        fill_color = "#f8717120"

    # Create fill area (close the path at the bottom)
    fill_points = polyline_points + f" {padding + chart_width:.1f},{padding + chart_height:.1f} {padding:.1f},{padding + chart_height:.1f}"

    # Format values for display
    current_val = values[-1]
    if current_val >= 1000000:
        val_display = f"${current_val/1000000:.2f}M"
    elif current_val >= 1000:
        val_display = f"${current_val/1000:.1f}K"
    else:
        val_display = f"${current_val:.0f}"

    trend_display = f"{'+'if trend_pct >= 0 else ''}{trend_pct:.1f}%"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height + 20}" viewBox="0 0 {width} {height + 20}" style="display:block;">
    <polygon points="{fill_points}" fill="{fill_color}" />
    <polyline points="{polyline_points}" fill="none" stroke="{line_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
    <circle cx="{points[-1].split(',')[0]}" cy="{points[-1].split(',')[1]}" r="3" fill="{line_color}" />
    <text x="{width/2}" y="{height + 14}" text-anchor="middle" font-family="-apple-system, sans-serif" font-size="11" fill="#94a3b8">
        <tspan fill="#e2e8f0" font-weight="600">{val_display}</tspan>
        <tspan fill="{line_color}" font-weight="600" dx="6">{trend_display}</tspan>
        <tspan fill="#64748b" dx="6">30d</tspan>
    </text>
</svg>"""

    return svg
