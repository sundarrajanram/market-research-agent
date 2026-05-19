"""Daily Market Research Agent - Main entry point."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from data_sources.market_data import (
    get_stock_data,
    get_index_performance,
    get_sector_performance,
)
from data_sources.news_sentiment import (
    get_market_news,
    get_fear_greed_index,
    get_reddit_sentiment,
)
from data_sources.motley_fool import MotleyFoolScraper
from analysis.technical import score_stock, classify_signal
from analysis.fundamental import score_fundamentals
from analysis.ai_synthesis import generate_ai_summary
from report.generator import generate_report
from email_sender import send_report
import config


def run_research():
    """Execute the full research pipeline."""
    print(f"[{datetime.now()}] Starting daily market research...")

    # 1. Market indices
    print("  Fetching market indices...")
    indices = get_index_performance(config.INDICES)
    index_names = {
        "^GSPC": "S&P 500",
        "^DJI": "Dow Jones",
        "^IXIC": "NASDAQ",
        "^VIX": "VIX",
        "^RUT": "Russell 2000",
    }
    indices = {index_names.get(k, k): v for k, v in indices.items()}

    # 2. Sector performance
    print("  Fetching sector performance...")
    sectors = get_sector_performance(config.SECTORS_ETFS)

    # 3. Stock data for watchlist
    print("  Fetching watchlist stock data...")
    stock_data = get_stock_data(config.WATCHLIST)

    # 4. Score and rank stocks
    print("  Running analysis...")
    scored_stocks = []
    for symbol, data in stock_data.items():
        tech = score_stock(data)
        fund = score_fundamentals(data)
        total_score = tech["score"] + fund["score"]
        all_signals = tech["signals"] + fund["signals"]
        rating = classify_signal(total_score)

        scored_stocks.append({
            "symbol": symbol,
            "name": data.get("name", symbol),
            "price": data["price"],
            "change_pct": data["change_pct"],
            "total_score": total_score,
            "rating": rating,
            "signals": all_signals,
            "sector": data.get("sector", "Unknown"),
        })

    scored_stocks.sort(key=lambda x: x["total_score"], reverse=True)
    top_picks = scored_stocks[:10]

    # 5. News and sentiment
    print("  Fetching news and sentiment...")
    news = get_market_news()
    fear_greed = get_fear_greed_index()
    reddit_trending = get_reddit_sentiment()

    # 6. Motley Fool
    print("  Fetching Motley Fool insights...")
    fool_picks = []
    if config.FOOL_EMAIL and config.FOOL_PASSWORD:
        fool = MotleyFoolScraper(config.FOOL_EMAIL, config.FOOL_PASSWORD)
        fool_picks = fool.get_stock_advisor_picks()
        fool_picks += fool.get_free_articles()

    # 7. AI synthesis
    print("  Generating AI market narrative...")
    report_data = {
        "indices": indices,
        "sectors": sectors,
        "top_picks": top_picks,
        "fear_greed": fear_greed,
        "news": news,
        "reddit_trending": reddit_trending,
        "fool_picks": fool_picks,
    }
    ai_summary = generate_ai_summary(report_data)
    report_data["ai_summary"] = ai_summary

    # 8. Generate report
    print("  Generating report...")
    html_report = generate_report(report_data)

    # 9. Send or save report
    print("  Sending report...")
    send_report(html_report)

    print(f"[{datetime.now()}] Research complete!")
    return report_data


if __name__ == "__main__":
    run_research()
