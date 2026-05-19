"""AI-powered market narrative using Groq (free tier - Llama 3)."""
import os
from groq import Groq


def generate_ai_summary(report_data):
    """Use Groq to generate a smart, portfolio-specific morning briefing."""
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
        context_parts.append("\nSECTOR PERFORMANCE (weekly):")
        for sector, data in sectors.items():
            context_parts.append(f"  {sector}: Daily {data['daily_change']:+.2f}%, Weekly {data['weekly_change']:+.2f}%")

    fear_greed = report_data.get("fear_greed")
    if fear_greed:
        context_parts.append(f"\nSENTIMENT: Fear & Greed {fear_greed['score']}/100 ({fear_greed['rating']})")

    portfolio_actions = report_data.get("portfolio_actions", [])
    if portfolio_actions:
        context_parts.append("\nPORTFOLIO HOLDINGS (stocks the investor owns):")
        for stock in portfolio_actions:
            context_parts.append(
                f"  {stock['symbol']} ({stock['name']}): ${stock['price']} ({stock['change_pct']:+.2f}%), "
                f"Score: {stock['total_score']}, Signal: {stock['action']}"
            )
            if stock.get("signals"):
                context_parts.append(f"    Technicals: {', '.join(stock['signals'][:3])}")
            context_parts.append(f"    Sector: {stock.get('sector', 'Unknown')}")

    opportunities = report_data.get("opportunities", [])
    if opportunities:
        context_parts.append("\nTOP OPPORTUNITIES (stocks NOT in portfolio):")
        for stock in opportunities[:5]:
            context_parts.append(
                f"  {stock['symbol']} ({stock['name']}): ${stock['price']} ({stock['change_pct']:+.2f}%), "
                f"Score: {stock['total_score']}, Rating: {stock['rating']}, Sector: {stock.get('sector', 'Unknown')}"
            )

    earnings_alerts = report_data.get("earnings_alerts", [])
    if earnings_alerts:
        context_parts.append("\nEARNINGS COMING UP:")
        for alert in earnings_alerts:
            context_parts.append(f"  {alert['symbol']} reports in {alert['days_until']} days ({alert['earnings_date']})")

    price_alerts = report_data.get("price_alerts", [])
    if price_alerts:
        context_parts.append("\nPRICE ALERTS:")
        for pa in price_alerts:
            alerts_text = ", ".join(a["message"] for a in pa.get("alerts", []))
            context_parts.append(f"  {pa['symbol']}: {alerts_text}")

    news = report_data.get("news", [])
    if news:
        context_parts.append("\nTODAY'S HEADLINES:")
        for article in news[:10]:
            context_parts.append(f"  - {article['title']} ({article['source']})")

    context = "\n".join(context_parts)

    prompt = f"""You are an elite portfolio advisor writing a personalized pre-market briefing for a retail investor.
The investor's actual holdings are listed below. Your job is to connect market events to THEIR specific stocks.

Write the briefing in this EXACT format (use the headers as shown):

**Market Mood:** [One sentence: bullish/bearish/mixed and why — reference specific index moves or sentiment]

**Your Stocks Today:**
[For each portfolio stock that has something notable happening (not all of them, only the 3-5 most relevant), write ONE line with the ticker and a specific, opinionated take. Explain WHY the signal exists — don't just repeat the score. Connect it to sector moves, news, or technicals. If a stock is TRIM/EXIT, explain what specifically is wrong and at what level you'd reconsider.]

**Headlines That Matter To You:**
[Pick 2-3 of today's headlines that DIRECTLY affect their holdings. Name the ticker and explain the connection. Skip headlines that don't impact their portfolio. If an earnings report is coming for one of their stocks, mention what to expect.]

**Today's Play:** [One specific, actionable trade idea with a price level if possible. "Buy X on any dip below $Y because Z" or "Trim X above $Y — momentum fading." Be bold.]

RULES:
- Never repeat what the data already says ("score is 25"). Instead explain the WHY behind it.
- Be specific to their stocks — no generic "stay diversified" advice
- If a stock is weak, say whether it's a buy-the-dip or a genuine deterioration
- Connect sector rotation to their specific holdings
- If nothing notable is happening with a stock, skip it
- Max 350 words total. Tight and punchy.

DATA:
{context}

Write the briefing now:"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=700,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq API error: {e}")
        return None
