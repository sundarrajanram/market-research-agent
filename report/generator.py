"""Generate the daily investment report — professional dark theme."""
import re
from datetime import datetime
from jinja2 import Template


def format_ai_html(text):
    """Convert AI markdown output to styled HTML with color coding."""
    if not text:
        return ""

    # Convert **bold headers** like **Market Mood:** to h3 tags
    text = re.sub(
        r'\*\*([^*]+?):\*\*',
        r'<h3>\1</h3>',
        text
    )
    # Convert remaining **bold** to strong tags
    text = re.sub(r'\*\*([^*]+?)\*\*', r'<strong>\1</strong>', text)

    # Color-code ticker symbols (uppercase 2-5 letter words preceded by common patterns)
    text = re.sub(
        r'\b([A-Z]{2,5})\b(?=[^<]*(?:<|$))',
        lambda m: f'<strong style="color: #e2e8f0;">{m.group(1)}</strong>'
        if m.group(1) in _TICKERS else m.group(0),
        text
    )

    # Color-code positive percentages
    text = re.sub(
        r'(\+\d+\.?\d*%)',
        r'<span style="color: #34d399; font-weight: 600;">\1</span>',
        text
    )
    # Color-code negative percentages
    text = re.sub(
        r'(-\d+\.?\d*%)',
        r'<span style="color: #f87171; font-weight: 600;">\1</span>',
        text
    )

    # Color-code dollar amounts
    text = re.sub(
        r'(\$\d[\d,.]*)',
        r'<span style="color: #fbbf24; font-weight: 500;">\1</span>',
        text
    )

    # Convert bullet points (- item) to list items
    lines = text.split('\n')
    result = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- ') or stripped.startswith('• '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(f'<li>{stripped[2:]}</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            if stripped.startswith('<h3>'):
                result.append(stripped)
            elif stripped:
                result.append(f'<p>{stripped}</p>')
            else:
                result.append('')
    if in_list:
        result.append('</ul>')

    return '\n'.join(result)


_TICKERS = {
    'VEEV', 'MGNI', 'NOW', 'VST', 'MSFT', 'TSLA', 'RKLB', 'EMBJ', 'MOG',
    'AAPL', 'GOOGL', 'AMZN', 'NVDA', 'META', 'AMD', 'NFLX', 'AVGO',
    'JPM', 'UNH', 'XOM', 'JNJ', 'WMT', 'CRM', 'COST', 'HD',
    'ABBV', 'PG', 'MA', 'SPY', 'QQQ', 'DIA', 'IWM', 'VIX',
}

REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif; background: #0a0e17; color: #e2e8f0; padding: 20px; line-height: 1.5; }
    .container { max-width: 720px; margin: 0 auto; }

    .header { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border: 1px solid #1e40af; border-radius: 12px; padding: 28px; margin-bottom: 16px; position: relative; overflow: hidden; }
    .header::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #3b82f6, #8b5cf6, #06b6d4); }
    .header h1 { font-size: 22px; font-weight: 700; color: #f8fafc; letter-spacing: -0.5px; }
    .header .subtitle { font-size: 13px; color: #64748b; margin-top: 4px; }
    .header .date { font-size: 14px; color: #94a3b8; margin-top: 8px; }

    .card { background: #111827; border: 1px solid #1f2937; border-radius: 10px; padding: 20px; margin-bottom: 12px; }
    .card h2 { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #64748b; margin-bottom: 14px; padding-bottom: 8px; border-bottom: 1px solid #1f2937; }

    .ai-brief { background: linear-gradient(135deg, #0c1a3a 0%, #111827 100%); border: 1px solid #1e3a5f; }
    .ai-brief h2 { color: #60a5fa; }
    .ai-brief .content { color: #cbd5e1; font-size: 14px; line-height: 1.7; }
    .ai-brief .content strong { color: #f8fafc; font-weight: 700; }
    .ai-brief .content h3 { color: #60a5fa; font-size: 13px; font-weight: 700; margin: 16px 0 8px; padding-top: 12px; border-top: 1px solid #1e3a5f; text-transform: uppercase; letter-spacing: 0.5px; }
    .ai-brief .content h3:first-child { margin-top: 0; padding-top: 0; border-top: none; }
    .ai-brief .content ul { list-style: none; padding: 0; margin: 8px 0; }
    .ai-brief .content li { padding: 4px 0 4px 12px; border-left: 2px solid #1e3a5f; margin-bottom: 6px; }
    .ai-brief .content p { margin: 8px 0; }

    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; }
    .metric-box { background: #0f172a; border: 1px solid #1f2937; border-radius: 8px; padding: 12px; text-align: center; }
    .metric-box .label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; }
    .metric-box .value { font-size: 18px; font-weight: 700; margin-top: 4px; }
    .metric-box .change { font-size: 12px; margin-top: 2px; }

    .sentiment-bar { height: 8px; border-radius: 4px; background: linear-gradient(90deg, #ef4444, #f59e0b, #22c55e); margin: 10px 0; position: relative; }
    .sentiment-marker { position: absolute; top: -4px; width: 16px; height: 16px; background: #fff; border-radius: 50%; border: 2px solid #0a0e17; transform: translateX(-50%); }

    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th { text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; padding: 8px 10px; border-bottom: 1px solid #1f2937; }
    td { padding: 10px; border-bottom: 1px solid #111827; }
    tr:hover { background: #0f172a; }

    .positive { color: #34d399; }
    .negative { color: #f87171; }

    .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
    .badge-add { background: #064e3b; color: #6ee7b7; }
    .badge-hold { background: #1e3a5f; color: #93c5fd; }
    .badge-watch { background: #3b3510; color: #fde68a; }
    .badge-trim { background: #4c1d1d; color: #fca5a5; }
    .badge-exit { background: #7f1d1d; color: #fecaca; }
    .badge-buy { background: #064e3b; color: #6ee7b7; }
    .badge-strong-buy { background: #052e16; color: #4ade80; border: 1px solid #16a34a; }
    .badge-sell { background: #4c1d1d; color: #fca5a5; }
    .badge-strong-sell { background: #7f1d1d; color: #fecaca; }
    .badge-new { background: #1e1b4b; color: #a5b4fc; }

    .stock-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #1f2937; }
    .stock-row:last-child { border-bottom: none; }
    .stock-info { flex: 1; }
    .stock-symbol { font-weight: 700; font-size: 14px; color: #f1f5f9; }
    .stock-name { font-size: 11px; color: #64748b; }
    .stock-price { font-size: 14px; font-weight: 600; text-align: right; }
    .stock-signals { margin-top: 4px; }
    .signal-tag { display: inline-block; font-size: 10px; background: #1f2937; color: #94a3b8; padding: 2px 6px; border-radius: 3px; margin: 2px 2px 0 0; }

    .action-row { display: flex; align-items: center; padding: 12px 0; border-bottom: 1px solid #1f2937; gap: 12px; }
    .action-row:last-child { border-bottom: none; }
    .action-detail { font-size: 11px; color: #64748b; margin-top: 2px; }

    .sector-bar { display: flex; align-items: center; padding: 6px 0; }
    .sector-name { width: 140px; font-size: 12px; color: #94a3b8; }
    .sector-value { font-size: 12px; font-weight: 600; width: 60px; text-align: right; }
    .sector-bar-track { flex: 1; height: 6px; background: #1f2937; border-radius: 3px; margin: 0 10px; overflow: hidden; }
    .sector-bar-fill { height: 100%; border-radius: 3px; }

    .news-item { padding: 8px 0; border-bottom: 1px solid #1f2937; }
    .news-item:last-child { border-bottom: none; }
    .news-item a { color: #93c5fd; text-decoration: none; font-size: 13px; }
    .news-item a:hover { color: #bfdbfe; }
    .news-source { font-size: 10px; color: #4b5563; margin-left: 8px; }

    .trending-tag { display: inline-block; background: #1f2937; border: 1px solid #374151; color: #d1d5db; padding: 4px 10px; border-radius: 16px; font-size: 11px; font-weight: 600; margin: 3px; }

    .footer { text-align: center; padding: 20px; font-size: 11px; color: #4b5563; }
    .footer a { color: #64748b; }

    .divider { height: 1px; background: linear-gradient(90deg, transparent, #1f2937, transparent); margin: 4px 0; }
</style>
</head>
<body>
<div class="container">

<div class="header">
    <h1>Market Intelligence Briefing</h1>
    <div class="subtitle">AI-Powered Daily Analysis</div>
    <div class="date">{{ date }} &bull; Pre-Market &bull; {{ generated_at }} PST</div>
</div>

{% if ai_summary %}
<div class="card ai-brief">
    <h2>Morning Briefing</h2>
    <div class="content">{{ ai_summary_html }}</div>
</div>
{% endif %}


{% if portfolio_actions %}
<div class="card">
    <h2>Your Portfolio &mdash; Today's Actions</h2>
    {% for stock in portfolio_actions %}
    <div class="action-row">
        <div>
            <span class="badge badge-{{ stock.action|lower|replace(' ', '-') }}">{{ stock.action }}</span>
        </div>
        <div class="stock-info">
            <a href="https://www.tradingview.com/symbols/{{ stock.symbol|replace('-', '.') }}/" style="text-decoration:none;">
                <span class="stock-symbol">{{ stock.symbol }}</span>
            </a>
            <span class="stock-name">{{ stock.name }}</span>
            <div class="action-detail">{{ stock.action_detail }}</div>
            <div style="margin-top: 4px;">
                {% for signal in stock.signals[:3] %}
                <span class="signal-tag">{{ signal }}</span>
                {% endfor %}
            </div>
            <div style="margin-top: 6px; font-size: 11px;">
                <a href="https://www.tradingview.com/symbols/{{ stock.symbol|replace('-', '.') }}/" style="color: #60a5fa; text-decoration: none; margin-right: 12px;">Chart</a>
                <a href="https://finance.yahoo.com/quote/{{ stock.symbol }}/" style="color: #60a5fa; text-decoration: none; margin-right: 12px;">Fundamentals</a>
                <a href="https://www.google.com/finance/quote/{{ stock.symbol }}:NASDAQ" style="color: #60a5fa; text-decoration: none; margin-right: 12px;">News</a>
                <a href="https://finviz.com/quote.ashx?t={{ stock.symbol }}" style="color: #60a5fa; text-decoration: none;">Analysis</a>
            </div>
        </div>
        <div class="stock-price">
            <div>${{ stock.price }}</div>
            <div class="{{ 'positive' if stock.change_pct >= 0 else 'negative' }}" style="font-size:12px;">
                {{ "+" if stock.change_pct >= 0 }}{{ stock.change_pct }}%
            </div>
            <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Score: {{ stock.total_score }}</div>
        </div>
    </div>
    {% endfor %}
</div>
{% endif %}

{% if earnings_alerts %}
<div class="card">
    <h2>Earnings Calendar - Upcoming</h2>
    <p style="font-size: 12px; color: #fbbf24; margin-bottom: 12px;">Portfolio stocks reporting earnings soon</p>
    {% for alert in earnings_alerts %}
    <div class="stock-row">
        <div class="stock-info">
            <span class="stock-symbol">{{ alert.symbol }}</span>
            <span style="font-size: 12px; color: #fbbf24; margin-left: 8px;">{{ alert.earnings_date }}</span>
        </div>
        <div style="text-align: right;">
            <span class="badge" style="background: #78350f; color: #fde68a;">
                {% if alert.days_until == 0 %}TODAY{% elif alert.days_until == 1 %}TOMORROW{% else %}{{ alert.days_until }} DAYS{% endif %}
            </span>
        </div>
    </div>
    {% endfor %}
</div>
{% endif %}

{% if insider_activity and insider_activity.trades %}
<div class="card">
    <h2>Insider Activity</h2>
    <p style="font-size: 12px; color: #64748b; margin-bottom: 12px;">Recent insider trades across your holdings — most recent first</p>

    {% if insider_activity.grouped.this_week %}
    <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #60a5fa; margin: 12px 0 8px; padding-top: 8px;">This Week</div>
    {% for trade in insider_activity.grouped.this_week %}
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #1f2937; font-size: 12px;">
        <div style="flex: 1;">
            <span class="badge {% if trade.type == 'BUY' %}badge-buy{% else %}badge-trim{% endif %}" style="font-size: 9px; margin-right: 4px;">{{ trade.type }}</span>
            <strong style="color: #f1f5f9;">{{ trade.symbol }}</strong>
            <span style="color: #94a3b8; margin-left: 6px;">{{ trade.insider }}</span>
            <span style="color: #4b5563; margin-left: 4px;">({{ trade.title }})</span>
        </div>
        <div style="text-align: right; white-space: nowrap;">
            <span style="color: #cbd5e1;">{{ trade.value }}</span>
            <span style="color: #4b5563; margin-left: 6px;">{{ trade.date }}</span>
        </div>
    </div>
    {% endfor %}
    {% endif %}

    {% if insider_activity.grouped.last_week %}
    <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #94a3b8; margin: 16px 0 8px; padding-top: 8px; border-top: 1px solid #1f2937;">Last Week</div>
    {% for trade in insider_activity.grouped.last_week %}
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #1f2937; font-size: 12px;">
        <div style="flex: 1;">
            <span class="badge {% if trade.type == 'BUY' %}badge-buy{% else %}badge-trim{% endif %}" style="font-size: 9px; margin-right: 4px;">{{ trade.type }}</span>
            <strong style="color: #f1f5f9;">{{ trade.symbol }}</strong>
            <span style="color: #94a3b8; margin-left: 6px;">{{ trade.insider }}</span>
            <span style="color: #4b5563; margin-left: 4px;">({{ trade.title }})</span>
        </div>
        <div style="text-align: right; white-space: nowrap;">
            <span style="color: #cbd5e1;">{{ trade.value }}</span>
            <span style="color: #4b5563; margin-left: 6px;">{{ trade.date }}</span>
        </div>
    </div>
    {% endfor %}
    {% endif %}

    {% if insider_activity.grouped.this_month %}
    <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; margin: 16px 0 8px; padding-top: 8px; border-top: 1px solid #1f2937;">This Month</div>
    {% for trade in insider_activity.grouped.this_month[:5] %}
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #1f2937; font-size: 12px;">
        <div style="flex: 1;">
            <span class="badge {% if trade.type == 'BUY' %}badge-buy{% else %}badge-trim{% endif %}" style="font-size: 9px; margin-right: 4px;">{{ trade.type }}</span>
            <strong style="color: #f1f5f9;">{{ trade.symbol }}</strong>
            <span style="color: #94a3b8; margin-left: 6px;">{{ trade.insider }}</span>
            <span style="color: #4b5563; margin-left: 4px;">({{ trade.title }})</span>
        </div>
        <div style="text-align: right; white-space: nowrap;">
            <span style="color: #cbd5e1;">{{ trade.value }}</span>
            <span style="color: #4b5563; margin-left: 6px;">{{ trade.date }}</span>
        </div>
    </div>
    {% endfor %}
    {% endif %}

    {% if insider_activity.grouped.older %}
    <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #4b5563; margin: 16px 0 8px; padding-top: 8px; border-top: 1px solid #1f2937;">Older</div>
    {% for trade in insider_activity.grouped.older[:3] %}
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #1f2937; font-size: 12px; opacity: 0.7;">
        <div style="flex: 1;">
            <span class="badge {% if trade.type == 'BUY' %}badge-buy{% else %}badge-trim{% endif %}" style="font-size: 9px; margin-right: 4px;">{{ trade.type }}</span>
            <strong style="color: #f1f5f9;">{{ trade.symbol }}</strong>
            <span style="color: #94a3b8; margin-left: 6px;">{{ trade.insider }}</span>
        </div>
        <div style="text-align: right; white-space: nowrap;">
            <span style="color: #cbd5e1;">{{ trade.value }}</span>
            <span style="color: #4b5563; margin-left: 6px;">{{ trade.date }}</span>
        </div>
    </div>
    {% endfor %}
    {% endif %}
</div>
{% endif %}

{% if price_alerts %}
<div class="card">
    <h2>Price Alerts</h2>
    {% for stock_alert in price_alerts %}
    <div style="margin-bottom: 10px;">
        <span class="stock-symbol">{{ stock_alert.symbol }}</span>
        <span style="font-size: 12px; color: #64748b; margin-left: 6px;">${{ stock_alert.price }}</span>
        <div style="margin-top: 4px;">
        {% for alert in stock_alert.alerts %}
            <span class="signal-tag" style="{% if alert.severity == 'bullish' %}background: #064e3b; color: #6ee7b7;{% elif alert.severity == 'bearish' %}background: #4c1d1d; color: #fca5a5;{% elif alert.severity == 'warning' %}background: #78350f; color: #fde68a;{% elif alert.severity == 'alert' %}background: #1e1b4b; color: #a5b4fc;{% endif %}">
                {{ alert.message }}
            </span>
        {% endfor %}
        </div>
    </div>
    {% endfor %}
</div>
{% endif %}

{% if opportunities %}
<div class="card">
    <h2>New Opportunities</h2>
    <p style="font-size: 12px; color: #64748b; margin-bottom: 12px;">High-scoring stocks not in your portfolio</p>
    {% for stock in opportunities %}
    <div class="stock-row">
        <div class="stock-info">
            <a href="https://www.tradingview.com/symbols/{{ stock.symbol|replace('-', '.') }}/" style="text-decoration:none;">
                <span class="stock-symbol">{{ stock.symbol }}</span>
            </a>
            <span class="stock-name">{{ stock.name }}</span>
            {% if position_sizing and position_sizing.suggestions %}
                {% for ps in position_sizing.suggestions %}
                    {% if ps.symbol == stock.symbol %}
                    <div style="margin-top: 4px; font-size: 11px; color: #a78bfa;">
                        Position size: ${{ "{:,.0f}".format(ps.suggested_amount) }} ({{ ps.suggested_shares }} shares) &bull; Conviction: {{ ps.conviction }}
                    </div>
                    {% endif %}
                {% endfor %}
            {% endif %}
            <div class="stock-signals">
                {% for signal in stock.signals[:3] %}
                <span class="signal-tag">{{ signal }}</span>
                {% endfor %}
            </div>
            <div style="margin-top: 6px; font-size: 11px;">
                <a href="https://www.tradingview.com/symbols/{{ stock.symbol|replace('-', '.') }}/" style="color: #60a5fa; text-decoration: none; margin-right: 12px;">Chart</a>
                <a href="https://finance.yahoo.com/quote/{{ stock.symbol }}/" style="color: #60a5fa; text-decoration: none; margin-right: 12px;">Fundamentals</a>
                <a href="https://finviz.com/quote.ashx?t={{ stock.symbol }}" style="color: #60a5fa; text-decoration: none;">Analysis</a>
            </div>
        </div>
        <div style="text-align: right;">
            <span class="badge badge-{{ stock.rating|lower|replace(' ', '-') }}">{{ stock.rating }}</span>
            <div class="stock-price" style="margin-top:4px;">
                ${{ stock.price }}
                <span class="{{ 'positive' if stock.change_pct >= 0 else 'negative' }}" style="font-size:12px;">
                    ({{ "+" if stock.change_pct >= 0 }}{{ stock.change_pct }}%)
                </span>
            </div>
            <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Score: {{ stock.total_score }}</div>
        </div>
    </div>
    {% endfor %}
    {% if position_sizing and position_sizing.total_portfolio_value %}
    <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #1f2937; font-size: 11px; color: #64748b;">
        Portfolio value: ${{ "{:,.0f}".format(position_sizing.total_portfolio_value) }} &bull; Position sizes based on conviction score
    </div>
    {% endif %}
</div>
{% endif %}


{% if fool_picks %}
<div class="card">
    <h2>Motley Fool Recommendations</h2>
    {% for pick in fool_picks[:8] %}
    <div class="news-item">
        <span class="badge badge-new" style="margin-right: 6px;">{{ pick.source }}</span>
        <strong style="color: #e2e8f0; font-size: 13px;">{{ pick.title }}</strong>
    </div>
    {% endfor %}
</div>
{% endif %}

{% if news %}
<div class="card">
    <h2>Market Headlines</h2>
    {% for article in news[:8] %}
    <div class="news-item">
        <a href="{{ article.link }}">{{ article.title }}</a>
        <span class="news-source">{{ article.source }}</span>
    </div>
    {% endfor %}
</div>
{% endif %}

{% if reddit_trending %}
<div class="card">
    <h2>Reddit Trending Tickers</h2>
    <div style="margin-top: 4px;">
    {% for ticker, count in reddit_trending[:12] %}
        <span class="trending-tag">${{ ticker }} <span style="color:#64748b;">({{ count }})</span></span>
    {% endfor %}
    </div>
</div>
{% endif %}

{% if indices or sectors %}
<div class="card">
    <h2>Market Overview</h2>
    <div style="display: flex; gap: 20px; flex-wrap: wrap;">
        {% if indices %}
        <div style="flex: 1; min-width: 280px;">
            <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; margin-bottom: 10px;">Indices</div>
            {% for name, data in indices.items() %}
            <div style="display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #1f2937;">
                <span style="font-size: 12px; color: #94a3b8;">{{ name }}</span>
                <span style="font-size: 12px;">
                    <span style="color: #cbd5e1;">${{ "{:,.0f}".format(data.price) }}</span>
                    <span class="{{ 'positive' if data.change_pct >= 0 else 'negative' }}" style="margin-left: 8px; font-weight: 600;">{{ "+" if data.change_pct >= 0 }}{{ data.change_pct }}%</span>
                </span>
            </div>
            {% endfor %}
            {% if fear_greed %}
            <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #1f2937;">
                <div style="font-size: 11px; color: #94a3b8; text-align: center;">
                    Fear & Greed: <strong style="color: #fbbf24;">{{ fear_greed.score|int }}/100</strong> ({{ fear_greed.rating }})
                </div>
                <div class="sentiment-bar" style="margin-top: 6px;">
                    <div class="sentiment-marker" style="left: {{ fear_greed.score }}%;"></div>
                </div>
            </div>
            {% endif %}
        </div>
        {% endif %}
        {% if sectors %}
        <div style="flex: 1; min-width: 280px;">
            <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; margin-bottom: 10px;">Sector Rotation (Weekly)</div>
            {% for sector, data in sectors.items() %}
            <div class="sector-bar">
                <span class="sector-name" style="width: 120px; font-size: 11px;">{{ sector }}</span>
                <div class="sector-bar-track">
                    {% if data.weekly_change >= 0 %}
                    <div class="sector-bar-fill" style="width: {{ [data.weekly_change * 5, 100]|min }}%; background: linear-gradient(90deg, #065f46, #34d399);"></div>
                    {% else %}
                    <div class="sector-bar-fill" style="width: {{ [(-data.weekly_change) * 5, 100]|min }}%; background: linear-gradient(90deg, #991b1b, #f87171);"></div>
                    {% endif %}
                </div>
                <span class="sector-value {{ 'positive' if data.weekly_change >= 0 else 'negative' }}" style="font-size: 11px;">{{ "+" if data.weekly_change >= 0 }}{{ data.weekly_change }}%</span>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
</div>
{% endif %}

{% if signal_accuracy and signal_accuracy.checked %}
<div class="card">
    <h2>Signal Accuracy Tracker</h2>
    <div style="display: flex; gap: 12px;">
        <div style="flex:1; background: #0f172a; border: 1px solid #1f2937; border-radius: 6px; padding: 10px; text-align: center;">
            <div style="font-size: 10px; color: #64748b; text-transform: uppercase;">Accuracy</div>
            <div style="font-size: 20px; font-weight: 700; color: {{ '#34d399' if signal_accuracy.accuracy_pct >= 60 else ('#fbbf24' if signal_accuracy.accuracy_pct >= 45 else '#f87171') }};">{{ signal_accuracy.accuracy_pct }}%</div>
        </div>
        <div style="flex:1; background: #0f172a; border: 1px solid #1f2937; border-radius: 6px; padding: 10px; text-align: center;">
            <div style="font-size: 10px; color: #64748b; text-transform: uppercase;">Correct</div>
            <div style="font-size: 20px; font-weight: 700; color: #34d399;">{{ signal_accuracy.correct }}</div>
        </div>
        <div style="flex:1; background: #0f172a; border: 1px solid #1f2937; border-radius: 6px; padding: 10px; text-align: center;">
            <div style="font-size: 10px; color: #64748b; text-transform: uppercase;">Checked</div>
            <div style="font-size: 20px; font-weight: 700; color: #94a3b8;">{{ signal_accuracy.checked }}</div>
        </div>
        <div style="flex:1; background: #0f172a; border: 1px solid #1f2937; border-radius: 6px; padding: 10px; text-align: center;">
            <div style="font-size: 10px; color: #64748b; text-transform: uppercase;">Total Signals</div>
            <div style="font-size: 20px; font-weight: 700; color: #94a3b8;">{{ signal_accuracy.total_signals }}</div>
        </div>
    </div>
    <div style="font-size: 10px; color: #4b5563; margin-top: 8px;">Signals verified after 7-day holding period</div>
</div>
{% endif %}

<div class="footer">
    <div class="divider"></div>
    <p style="margin-top: 12px;">This report is for informational purposes only. Not financial advice. Always DYOR.</p>
    <p style="margin-top: 4px;">Generated by Market Intelligence Agent &bull; {{ generated_at }} PST</p>
</div>

</div>
</body>
</html>
"""


def generate_report(data):
    """Generate HTML report from collected data."""
    template = Template(REPORT_TEMPLATE)

    ai_raw = data.get("ai_summary")
    ai_html = format_ai_html(ai_raw) if ai_raw else ""

    return template.render(
        date=datetime.now().strftime("%B %d, %Y"),
        generated_at=datetime.now().strftime("%I:%M %p"),
        ai_summary=ai_raw,
        ai_summary_html=ai_html,
        fear_greed=data.get("fear_greed"),
        indices=data.get("indices", {}),
        sectors=data.get("sectors", {}),
        portfolio_actions=data.get("portfolio_actions", []),
        opportunities=data.get("opportunities", []),
        fool_picks=data.get("fool_picks", []),
        fool_articles=data.get("fool_articles", []),
        news=data.get("news", []),
        reddit_trending=data.get("reddit_trending", []),
        earnings_alerts=data.get("earnings_alerts", []),
        insider_activity=data.get("insider_activity", {}),
        price_alerts=data.get("price_alerts", []),
        position_sizing=data.get("position_sizing", {}),
        signal_accuracy=data.get("signal_accuracy", {}),
    )
