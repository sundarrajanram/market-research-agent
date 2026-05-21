"""Generate Gmail-compatible mini sparklines for each portfolio stock."""
import yfinance as yf
from data_sources.portfolio_loader import load_portfolio


def generate_portfolio_sparkline(height=24):
    """Generate a compact row of mini bar charts — one per portfolio stock."""
    portfolio = load_portfolio()
    if not portfolio:
        return ""

    stock_charts = []

    for holding in portfolio:
        symbol = holding["symbol"]
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")
            if hist.empty or len(hist) < 5:
                continue

            values = hist["Close"].values.tolist()
            min_val = min(values)
            max_val = max(values)
            val_range = max_val - min_val if max_val != min_val else 1

            # 30-day trend
            trend_pct = ((values[-1] - values[0]) / values[0]) * 100
            bar_color = "#34d399" if trend_pct >= 0 else "#f87171"
            trend_display = f"{'+'if trend_pct >= 0 else ''}{trend_pct:.0f}%"

            # Sample to 10 bars
            num_bars = 10
            step = max(1, len(values) // num_bars)
            sampled = values[::step][-num_bars:]

            # Build mini bars
            bars_html = ""
            for val in sampled:
                pct = (val - min_val) / val_range
                h = max(2, int(pct * height))
                bars_html += (
                    f'<td style="vertical-align:bottom;padding:0 0.5px;">'
                    f'<div style="width:3px;height:{h}px;background:{bar_color};border-radius:1px 1px 0 0;"></div>'
                    f'</td>'
                )

            stock_html = f"""<div style="display:inline-block;text-align:center;margin:0 6px 8px 0;">
    <table cellpadding="0" cellspacing="0" border="0" style="margin:0 auto;"><tr>{bars_html}</tr></table>
    <div style="font-size:9px;margin-top:2px;">
        <span style="color:#e2e8f0;font-weight:700;">{symbol.replace('-', '.')}</span>
        <span style="color:{bar_color};font-weight:600;margin-left:2px;">{trend_display}</span>
    </div>
</div>"""
            stock_charts.append(stock_html)

        except Exception:
            continue

    if not stock_charts:
        return ""

    return "\n".join(stock_charts)
