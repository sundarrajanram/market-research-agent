"""AI-powered market narrative using Groq (free tier - Llama 3)."""
import os
from groq import Groq


def generate_ai_summary(report_data):
    """Use Groq to generate a narrative market analysis."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    client = Groq(api_key=api_key)

    context_parts = []

    indices = report_data.get("indices", {})
    if indices:
        context_parts.append("MARKET INDICES:")
        for name, data in indices.items():
            context_parts.append(f"  {name}: ${data['price']:,.2f} ({data['change_pct']:+.2f}%)")

    sectors = report_data.get("sectors", {})
    if sectors:
        context_parts.append("\nSECTOR PERFORMANCE:")
        for sector, data in sectors.items():
            context_parts.append(f"  {sector}: Daily {data['daily_change']:+.2f}%, Weekly {data['weekly_change']:+.2f}%")

    fear_greed = report_data.get("fear_greed")
    if fear_greed:
        context_parts.append(f"\nMARKET SENTIMENT: Fear & Greed Index: {fear_greed['score']}/100 ({fear_greed['rating']})")

    portfolio_actions = report_data.get("portfolio_actions", [])
    if portfolio_actions:
        context_parts.append("\nYOUR PORTFOLIO (stocks you own):")
        for stock in portfolio_actions:
            context_parts.append(
                f"  {stock['symbol']} ({stock['name']}): ${stock['price']} ({stock['change_pct']:+.2f}%), "
                f"Score: {stock['total_score']}, Action: {stock['action']}"
            )
            if stock.get("signals"):
                context_parts.append(f"    Key signals: {', '.join(stock['signals'][:2])}")

    opportunities = report_data.get("opportunities", [])
    if opportunities:
        context_parts.append("\nTOP OPPORTUNITIES (stocks NOT in your portfolio):")
        for stock in opportunities[:5]:
            context_parts.append(
                f"  {stock['symbol']} ({stock['name']}): ${stock['price']} ({stock['change_pct']:+.2f}%), "
                f"Score: {stock['total_score']}, Signal: {stock['rating']}"
            )

    news = report_data.get("news", [])
    if news:
        context_parts.append("\nKEY HEADLINES:")
        for article in news[:6]:
            context_parts.append(f"  - {article['title']}")

    context = "\n".join(context_parts)

    prompt = f"""You are a professional portfolio advisor writing a personalized pre-market briefing.
The investor owns specific stocks (listed below). Your analysis must be tailored to THEIR portfolio.

Based on the data below, write a concise (300-400 words) morning briefing that:

1. Opens with a 1-sentence market mood summary
2. YOUR PORTFOLIO TODAY (2-3 sentences): What's happening with their specific holdings today. Which are looking strong, which need attention.
3. ACTION ITEMS (bullet points): Specific recommendations for their portfolio — what to add, hold, trim, or exit and WHY
4. NEW OPPORTUNITIES (2-3 stocks): High-conviction ideas they don't own yet with a one-line thesis
5. RISK WATCH: One key risk or event to monitor today
6. Closes with "Today's Play:" — one specific actionable trade idea

Be direct, confident, and specific. Name ticker symbols. No generic advice or disclaimers.

DATA:
{context}

Write the briefing:"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=600,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq API error: {e}")
        return None
