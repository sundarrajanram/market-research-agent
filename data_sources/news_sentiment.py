"""Fetch market news and sentiment from free sources."""
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


def get_market_news():
    """Aggregate market news from RSS feeds."""
    feeds = {
        "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
        "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
        "MarketWatch": "http://feeds.marketwatch.com/marketwatch/topstories/",
        "CNBC": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    }

    articles = []
    for source, url in feeds.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                articles.append({
                    "source": source,
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", "")[:200],
                })
        except Exception as e:
            print(f"Error fetching {source}: {e}")

    return articles


def get_fear_greed_index():
    """Get CNN Fear & Greed Index."""
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            score = data.get("fear_and_greed", {}).get("score")
            rating = data.get("fear_and_greed", {}).get("rating")
            return {"score": score, "rating": rating}
    except Exception as e:
        print(f"Error fetching Fear & Greed: {e}")
    return None


def get_reddit_sentiment(subreddits=None):
    """Get trending tickers from Reddit (no auth required, uses RSS)."""
    if subreddits is None:
        subreddits = ["wallstreetbets", "stocks", "investing"]

    mentions = {}
    for sub in subreddits:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit=25"
            headers = {"User-Agent": "MarketResearchBot/1.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                posts = resp.json().get("data", {}).get("children", [])
                for post in posts:
                    title = post["data"].get("title", "")
                    for word in title.split():
                        clean = word.strip("$.,!?()[]").upper()
                        if 2 <= len(clean) <= 5 and clean.isalpha():
                            mentions[clean] = mentions.get(clean, 0) + 1
        except Exception as e:
            print(f"Error fetching r/{sub}: {e}")

    sorted_mentions = sorted(mentions.items(), key=lambda x: x[1], reverse=True)
    return sorted_mentions[:20]


def get_economic_calendar():
    """Get upcoming economic events from FRED/news sources."""
    events = []
    try:
        feed = feedparser.parse("https://www.federalreserve.gov/feeds/press_all.xml")
        for entry in feed.entries[:5]:
            events.append({
                "title": entry.get("title", ""),
                "date": entry.get("published", ""),
                "source": "Federal Reserve",
            })
    except Exception:
        pass
    return events
