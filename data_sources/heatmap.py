"""Portfolio heatmap generator — TradingView-style treemap using email-safe tables."""


def _change_to_color(change_pct):
    """Map daily change % to TradingView-style red/green. Neutral is dark gray."""
    clamped = max(-5.0, min(5.0, change_pct))
    intensity = abs(clamped) / 5.0

    if abs(clamped) < 0.05:
        return "#2a2e39"

    if clamped > 0:
        if intensity > 0.6:
            r, g, b = 34, 171, 101
        elif intensity > 0.3:
            r = int(38 + (34 - 38) * ((intensity - 0.3) / 0.3))
            g = int(100 + (171 - 100) * ((intensity - 0.3) / 0.3))
            b = int(69 + (101 - 69) * ((intensity - 0.3) / 0.3))
        else:
            r = int(42 + (38 - 42) * (intensity / 0.3))
            g = int(56 + (100 - 56) * (intensity / 0.3))
            b = int(48 + (69 - 48) * (intensity / 0.3))
        return f"rgb({r}, {g}, {b})"
    else:
        if intensity > 0.6:
            r, g, b = 204, 51, 51
        elif intensity > 0.3:
            r = int(140 + (204 - 140) * ((intensity - 0.3) / 0.3))
            g = int(40 + (51 - 40) * ((intensity - 0.3) / 0.3))
            b = int(40 + (51 - 40) * ((intensity - 0.3) / 0.3))
        else:
            r = int(70 + (140 - 70) * (intensity / 0.3))
            g = int(42 + (40 - 42) * (intensity / 0.3))
            b = int(42 + (40 - 42) * (intensity / 0.3))
        return f"rgb({r}, {g}, {b})"


def _layout_rows(holdings):
    """Lay out holdings into rows for a treemap-like grid.

    Larger holdings get taller rows. Each row tries to fill ~100% width
    by grouping items whose allocations sum to a reasonable row target.
    """
    total_alloc = sum(h["allocation_pct"] for h in holdings)
    if total_alloc <= 0:
        return []

    rows = []
    current_row = []
    current_row_pct = 0
    target_row_pct = 40

    for h in holdings:
        current_row.append(h)
        current_row_pct += h["allocation_pct"]

        if current_row_pct >= target_row_pct and len(current_row) >= 2:
            rows.append((current_row, current_row_pct))
            current_row = []
            current_row_pct = 0
        elif len(current_row) >= 5:
            rows.append((current_row, current_row_pct))
            current_row = []
            current_row_pct = 0

    if current_row:
        rows.append((current_row, current_row_pct))

    return rows


def generate_heatmap_html(holdings_data):
    """Generate a TradingView-style treemap heatmap as email-safe HTML (tables only).

    holdings_data: list of dicts with keys:
        - symbol: str
        - allocation_pct: float (% of portfolio)
        - change_pct: float (daily % change)
    """
    if not holdings_data:
        return ""

    sorted_holdings = sorted(holdings_data, key=lambda x: x["allocation_pct"], reverse=True)
    sorted_holdings = [h for h in sorted_holdings if h["allocation_pct"] > 0]

    if not sorted_holdings:
        return ""

    total_alloc = sum(h["allocation_pct"] for h in sorted_holdings)
    rows = _layout_rows(sorted_holdings)

    total_height = 260
    rows_html = ""

    for row_holdings, row_pct in rows:
        row_height = max(40, int((row_pct / total_alloc) * total_height))

        cells_html = ""
        for h in row_holdings:
            width_pct = (h["allocation_pct"] / row_pct) * 100 if row_pct > 0 else 0
            bg_color = _change_to_color(h["change_pct"])
            sign = "+" if h["change_pct"] >= 0 else ""

            if width_pct < 8 or row_height < 30:
                label = (
                    f'<span style="font-size:9px;font-weight:700;color:#fff;">'
                    f'{h["symbol"][:4]}</span>'
                )
            elif width_pct < 15:
                label = (
                    f'<span style="font-size:11px;font-weight:700;color:#fff;">'
                    f'{h["symbol"]}</span>'
                )
            else:
                label = (
                    f'<span style="font-size:13px;font-weight:700;color:#fff;display:block;'
                    f'line-height:1.2;">{h["symbol"]}</span>'
                    f'<span style="font-size:11px;color:rgba(255,255,255,0.9);display:block;'
                    f'line-height:1.3;">{sign}{h["change_pct"]}%</span>'
                )

            cells_html += (
                f'<td style="width:{width_pct:.1f}%;height:{row_height}px;'
                f'background:{bg_color};text-align:center;vertical-align:middle;'
                f'padding:2px 1px;border:1px solid #131722;overflow:hidden;'
                f'max-width:0;word-break:break-all;">'
                f'{label}</td>'
            )

        rows_html += f'<tr>{cells_html}</tr>'

    html = (
        f'<div style="background:#111827;border:1px solid #1f2937;border-radius:10px;'
        f'padding:16px;margin-bottom:12px;">'
        f'<table style="font-size:10px;font-weight:600;text-transform:uppercase;'
        f'letter-spacing:0.5px;color:#64748b;margin-bottom:10px;border:0;">'
        f'<tr><td>Portfolio Heatmap</td></tr></table>'
        f'<table width="100%" cellpadding="0" cellspacing="0" '
        f'style="border-collapse:collapse;table-layout:fixed;width:100%;">'
        f'{rows_html}'
        f'</table>'
        f'<table style="margin-top:8px;font-size:9px;color:#64748b;width:100%;border:0;">'
        f'<tr><td style="text-align:left;">Size = position weight &bull; Color = daily P&L</td>'
        f'<td style="text-align:right;">'
        f'<span style="display:inline-block;width:10px;height:10px;'
        f'background:rgb(204,51,51);vertical-align:middle;"></span> Loss'
        f'&nbsp;&nbsp;'
        f'<span style="display:inline-block;width:10px;height:10px;'
        f'background:rgb(34,171,101);vertical-align:middle;"></span> Gain'
        f'</td></tr></table>'
        f'</div>'
    )

    return html
