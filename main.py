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
from data_sources.alerts import (
    get_earnings_alerts,
    get_insider_activity,
    get_price_alerts,
    calculate_position_sizes,
    log_signals,
    check_signal_accuracy,
)
from data_sources.motley_fool import MotleyFoolScraper
from data_sources.portfolio_loader import load_portfolio
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

    # 3. Load portfolio + Motley Fool recommendations
    print("  Loading portfolio...")
    my_portfolio = load_portfolio()
    print(f"    Found {len(my_portfolio)} holdings in portfolio")

    print("  Fetching Motley Fool insights...")
    fool_picks = []
    fool_articles = []
    if config.FOOL_EMAIL and config.FOOL_PASSWORD:
        fool = MotleyFoolScraper(config.FOOL_EMAIL, config.FOOL_PASSWORD)
        fool_picks = fool.get_stock_advisor_picks()
        fool_picks += fool.get_rule_breakers_picks()
        fool_articles = fool.get_free_articles()

    # 4. Build combined watchlist (portfolio + default watchlist)
    portfolio_symbols = [h["symbol"] for h in my_portfolio if h.get("symbol")]
    all_symbols = list(set(config.WATCHLIST + portfolio_symbols))

    # 5. Stock data
    print("  Fetching stock data...")
    stock_data = get_stock_data(all_symbols)

    # 6. Score and rank all stocks
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

    # 7. Separate portfolio stocks from opportunities
    portfolio_scored = [s for s in scored_stocks if s["symbol"] in portfolio_symbols]
    portfolio_scored.sort(key=lambda x: x["total_score"], reverse=True)

    # Top opportunities NOT in portfolio
    opportunities = [s for s in scored_stocks if s["symbol"] not in portfolio_symbols][:8]

    # Portfolio action items
    portfolio_actions = []
    for stock in portfolio_scored:
        if stock["total_score"] >= 30:
            action = "ADD MORE"
            action_detail = "Strong signals — consider increasing position"
        elif stock["total_score"] >= 10:
            action = "HOLD"
            action_detail = "Positive outlook — maintain current position"
        elif stock["total_score"] >= -10:
            action = "WATCH"
            action_detail = "Neutral signals — monitor closely"
        elif stock["total_score"] >= -30:
            action = "TRIM"
            action_detail = "Weakening signals — consider reducing"
        else:
            action = "EXIT"
            action_detail = "Negative signals — consider selling"

        portfolio_actions.append({
            **stock,
            "action": action,
            "action_detail": action_detail,
        })

    # 8. News and sentiment
    print("  Fetching news and sentiment...")
    news = get_market_news()
    fear_greed = get_fear_greed_index()
    reddit_trending = get_reddit_sentiment()

    # 9. New data sources (with graceful error handling)
    print("  Checking earnings calendar...")
    earnings_alerts = []
    try:
        earnings_alerts = get_earnings_alerts(portfolio_symbols)
    except Exception as e:
        print(f"    Earnings alerts failed (non-fatal): {e}")

    print("  Checking insider activity...")
    insider_activity = {}
    try:
        insider_activity = get_insider_activity(portfolio_symbols)
    except Exception as e:
        print(f"    Insider activity failed (non-fatal): {e}")

    print("  Checking price alerts...")
    price_alerts = []
    try:
        price_alerts = get_price_alerts(stock_data, portfolio_symbols)
    except Exception as e:
        print(f"    Price alerts failed (non-fatal): {e}")

    print("  Calculating position sizes...")
    position_sizing = {}
    try:
        position_sizing = calculate_position_sizes(my_portfolio, stock_data, opportunities)
    except Exception as e:
        print(f"    Position sizing failed (non-fatal): {e}")

    print("  Logging signals and checking history...")
    signal_accuracy = {}
    try:
        log_signals(scored_stocks)
        signal_accuracy = check_signal_accuracy()
    except Exception as e:
        print(f"    Signal history failed (non-fatal): {e}")

    # 10. AI synthesis
    print("  Generating AI market narrative...")
    report_data = {
        "indices": indices,
        "sectors": sectors,
        "portfolio_actions": portfolio_actions,
        "opportunities": opportunities,
        "top_picks": scored_stocks[:10],
        "fear_greed": fear_greed,
        "news": news,
        "reddit_trending": reddit_trending,
        "fool_picks": fool_picks,
        "fool_articles": fool_articles,
        "earnings_alerts": earnings_alerts,
        "insider_activity": insider_activity,
        "price_alerts": price_alerts,
        "position_sizing": position_sizing,
        "signal_accuracy": signal_accuracy,
    }
    ai_summary = generate_ai_summary(report_data)
    report_data["ai_summary"] = ai_summary

    # 11. Generate report
    print("  Generating report...")
    html_report = generate_report(report_data)

    # 12. Send or save report
    print("  Sending report...")
    send_report(html_report)

    print(f"[{datetime.now()}] Research complete!")
    return report_data


if __name__ == "__main__":
    run_research()
