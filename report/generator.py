"""Generate the daily investment report."""
from datetime import datetime
from jinja2 import Template

REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
    .header { background: linear-gradient(135deg, #1a237e, #0d47a1); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
    .header h1 { margin: 0; font-size: 24px; }
    .header p { margin: 5px 0 0; opacity: 0.8; }
    .section { background: white; padding: 20px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .section h2 { color: #1a237e; margin-top: 0; border-bottom: 2px solid #e3f2fd; padding-bottom: 10px; }
    .stock-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
    .stock-name { font-weight: 600; }
    .positive { color: #2e7d32; }
    .negative { color: #c62828; }
    .signal-badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
    .strong-buy { background: #e8f5e9; color: #1b5e20; }
    .buy { background: #f1f8e9; color: #33691e; }
    .hold { background: #fff8e1; color: #f57f17; }
    .sell { background: #fbe9e7; color: #bf360c; }
    .strong-sell { background: #ffebee; color: #b71c1c; }
    .indicator { display: inline-block; margin: 3px 5px 3px 0; padding: 2px 8px; background: #e3f2fd; border-radius: 4px; font-size: 11px; }
    .news-item { padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
    .news-source { font-size: 11px; color: #666; }
    .fear-greed { text-align: center; font-size: 48px; font-weight: bold; }
    .disclaimer { font-size: 11px; color: #999; text-align: center; margin-top: 20px; }
    table { width: 100%; border-collapse: collapse; }
    td, th { padding: 8px; text-align: left; border-bottom: 1px solid #eee; }
    th { font-weight: 600; color: #666; font-size: 12px; text-transform: uppercase; }
</style>
</head>
<body>
<div class="header">
    <h1>Daily Market Intelligence Report</h1>
    <p>{{ date }} | Pre-Market Analysis</p>
</div>

{% if ai_summary %}
<div class="section">
    <h2>AI Market Analysis</h2>
    <div style="line-height:1.6; color:#333; white-space:pre-wrap;">{{ ai_summary }}</div>
</div>
{% endif %}

{% if fear_greed %}
<div class="section">
    <h2>Market Sentiment</h2>
    <div class="fear-greed {{ fear_greed.rating|lower|replace(' ', '-') }}">
        {{ fear_greed.score|int }}/100
    </div>
    <p style="text-align:center; color:#666;">CNN Fear & Greed Index: <strong>{{ fear_greed.rating }}</strong></p>
</div>
{% endif %}

{% if indices %}
<div class="section">
    <h2>Market Indices</h2>
    <table>
        <tr><th>Index</th><th>Price</th><th>Change</th></tr>
        {% for name, data in indices.items() %}
        <tr>
            <td>{{ name }}</td>
            <td>${{ "{:,.2f}".format(data.price) }}</td>
            <td class="{{ 'positive' if data.change_pct >= 0 else 'negative' }}">
                {{ "+" if data.change_pct >= 0 }}{{ data.change_pct }}%
            </td>
        </tr>
        {% endfor %}
    </table>
</div>
{% endif %}

{% if sectors %}
<div class="section">
    <h2>Sector Performance</h2>
    <table>
        <tr><th>Sector</th><th>Daily</th><th>Weekly</th></tr>
        {% for sector, data in sectors.items() %}
        <tr>
            <td>{{ sector }}</td>
            <td class="{{ 'positive' if data.daily_change >= 0 else 'negative' }}">
                {{ "+" if data.daily_change >= 0 }}{{ data.daily_change }}%
            </td>
            <td class="{{ 'positive' if data.weekly_change >= 0 else 'negative' }}">
                {{ "+" if data.weekly_change >= 0 }}{{ data.weekly_change }}%
            </td>
        </tr>
        {% endfor %}
    </table>
</div>
{% endif %}

{% if top_picks %}
<div class="section">
    <h2>Top Investment Opportunities</h2>
    {% for pick in top_picks %}
    <div class="stock-row">
        <div>
            <span class="stock-name">{{ pick.symbol }}</span>
            <span style="color:#666; font-size:13px;"> - {{ pick.name }}</span><br>
            <span style="font-size:13px;">${{ pick.price }}
                <span class="{{ 'positive' if pick.change_pct >= 0 else 'negative' }}">
                    ({{ "+" if pick.change_pct >= 0 }}{{ pick.change_pct }}%)
                </span>
            </span><br>
            {% for signal in pick.signals[:3] %}
            <span class="indicator">{{ signal }}</span>
            {% endfor %}
        </div>
        <div>
            <span class="signal-badge {{ pick.rating|lower|replace(' ', '-') }}">{{ pick.rating }}</span><br>
            <span style="font-size:12px; color:#666;">Score: {{ pick.total_score }}</span>
        </div>
    </div>
    {% endfor %}
</div>
{% endif %}

{% if portfolio_summary %}
<div class="section">
    <h2>Your Robinhood Portfolio</h2>
    <table>
        <tr>
            <td><strong>Total Equity</strong></td>
            <td>${{ "{:,.2f}".format(portfolio_summary.equity) }}</td>
        </tr>
        <tr>
            <td><strong>Market Value</strong></td>
            <td>${{ "{:,.2f}".format(portfolio_summary.market_value) }}</td>
        </tr>
    </table>

    {% if holdings %}
    <h3 style="margin-top:15px; font-size:14px; color:#666;">Current Holdings</h3>
    <table>
        <tr><th>Symbol</th><th>Shares</th><th>Avg Cost</th><th>Current</th><th>Return</th></tr>
        {% for h in holdings[:15] %}
        <tr>
            <td><strong>{{ h.symbol }}</strong></td>
            <td>{{ "%.2f"|format(h.quantity) }}</td>
            <td>${{ "%.2f"|format(h.avg_cost) }}</td>
            <td>${{ "%.2f"|format(h.current_price) }}</td>
            <td class="{{ 'positive' if h.total_return_pct >= 0 else 'negative' }}">
                {{ "+" if h.total_return_pct >= 0 }}{{ "%.1f"|format(h.total_return_pct) }}%
            </td>
        </tr>
        {% endfor %}
    </table>
    {% endif %}
</div>
{% endif %}

{% if portfolio_suggestions %}
<div class="section">
    <h2>Portfolio Action Items</h2>
    {% for s in portfolio_suggestions %}
    <div class="stock-row" style="align-items:flex-start;">
        <div>
            <span class="signal-badge {% if s.type == 'WARNING' %}strong-sell{% elif s.type == 'REDUCE' %}sell{% elif s.type == 'ADD' %}buy{% elif s.type == 'NEW' %}strong-buy{% elif s.type == 'TAX' %}hold{% else %}hold{% endif %}">
                {{ s.type }}
            </span>
            <strong style="margin-left:8px;">{{ s.symbol }}</strong>
        </div>
        <div style="font-size:13px; color:#444; margin-top:4px;">{{ s.message }}</div>
    </div>
    {% endfor %}
</div>
{% endif %}

{% if fool_picks %}
<div class="section">
    <h2>Motley Fool Insights</h2>
    {% for pick in fool_picks %}
    <div class="news-item">
        <strong>{{ pick.title }}</strong>
        <span class="news-source">{{ pick.source }}</span>
    </div>
    {% endfor %}
</div>
{% endif %}

{% if news %}
<div class="section">
    <h2>Key Market News</h2>
    {% for article in news[:10] %}
    <div class="news-item">
        <a href="{{ article.link }}" style="text-decoration:none; color:#1a237e;">{{ article.title }}</a>
        <span class="news-source">{{ article.source }}</span>
    </div>
    {% endfor %}
</div>
{% endif %}

{% if reddit_trending %}
<div class="section">
    <h2>Trending on Reddit</h2>
    <p style="font-size:13px; color:#666;">Most mentioned tickers in r/wallstreetbets, r/stocks, r/investing:</p>
    {% for ticker, count in reddit_trending[:10] %}
    <span class="indicator">{{ ticker }} ({{ count }})</span>
    {% endfor %}
</div>
{% endif %}

<div class="disclaimer">
    <p>This report is for informational purposes only and does not constitute financial advice.
    Always do your own research before making investment decisions. Past performance does not guarantee future results.</p>
    <p>Generated at {{ generated_at }} PST</p>
</div>
</body>
</html>
"""


def generate_report(data):
    """Generate HTML report from collected data."""
    template = Template(REPORT_TEMPLATE)
    return template.render(
        date=datetime.now().strftime("%B %d, %Y"),
        generated_at=datetime.now().strftime("%I:%M %p"),
        fear_greed=data.get("fear_greed"),
        indices=data.get("indices", {}),
        sectors=data.get("sectors", {}),
        top_picks=data.get("top_picks", []),
        fool_picks=data.get("fool_picks", []),
        news=data.get("news", []),
        reddit_trending=data.get("reddit_trending", []),
        ai_summary=data.get("ai_summary"),
    )
