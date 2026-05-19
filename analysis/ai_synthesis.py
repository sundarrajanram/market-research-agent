"""AI-powered market narrative using Groq (free tier - Llama 3)."""
import os
from groq import Groq


def generate_ai_summary(report_data):
    """Use Groq to generate a narrative market analysis."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    client = Groq(api_key=api_key)

    # Build context from report data
    context_parts = []

    indices = report_data.get("indices", {})
    if indices:
        context_parts.append("Market Indices Today:")
        for name, data in indices.items():
            context_parts.append(f"  {name}: ${data['price']:,.2f} ({data['change_pct']:+.2f}%)")

    sectors = report_data.get("sectors", {})
    if sectors:
        context_parts.append("\nSector Performance:")
        for sector, data in sectors.items():
            context_parts.append(f"  {sector}: Daily {data['daily_change']:+.2f}%, Weekly {data['weekly_change']:+.2f}%")

    fear_greed = report_data.get("fear_greed")
    if fear_greed:
        context_parts.append(f"\nFear & Greed Index: {fear_greed['score']}/100 ({fear_greed['rating']})")

    top_picks = report_data.get("top_picks", [])
    if top_picks:
        context_parts.append("\nTop Scored Stocks:")
        for pick in top_picks[:7]:
            context_parts.append(
                f"  {pick['symbol']} ({pick['name']}): ${pick['price']} ({pick['change_pct']:+.2f}%), "
                f"Score: {pick['total_score']}, Signal: {pick['rating']}"
            )
            if pick.get("signals"):
                context_parts.append(f"    Signals: {', '.join(pick['signals'][:3])}")

    news = report_data.get("news", [])
    if news:
        context_parts.append("\nKey Headlines:")
        for article in news[:8]:
            context_parts.append(f"  - {article['title']} ({article['source']})")

    context = "\n".join(context_parts)

    prompt = f"""You are a professional market analyst writing a pre-market briefing for a retail investor.
Based on the following data, write a concise (250-350 words) morning market analysis that:

1. Summarizes the current market mood and direction
2. Highlights 2-3 key opportunities or risks for today
3. Gives 2-3 specific actionable suggestions (what to buy, hold, or watch)
4. Notes any important sector rotations or momentum shifts
5. Ends with a one-line "Today's Strategy" recommendation

Be direct, specific, and confident. Use plain language. No disclaimers or hedging.

DATA:
{context}

Write the analysis now:"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq API error: {e}")
        return None
