"""Load portfolio — tries Snaptrade (live Robinhood) first, falls back to local JSON."""
import json
import os


def load_portfolio(filepath=None):
    """Load portfolio holdings. Tries Snaptrade first, then local file."""
    # Try Snaptrade (live Robinhood data)
    if os.getenv("SNAPTRADE_CLIENT_ID"):
        try:
            from data_sources.snaptrade_loader import load_portfolio_from_snaptrade
            holdings = load_portfolio_from_snaptrade()
            if holdings:
                print(f"    Loaded {len(holdings)} holdings from Robinhood (via Snaptrade)")
                return holdings
        except Exception as e:
            print(f"    Snaptrade failed, falling back to local file: {e}")

    # Fall back to local file
    if filepath is None:
        filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "portfolio.json")

    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        holdings = data.get("holdings", [])
        print(f"    Loaded {len(holdings)} holdings from portfolio.json (fallback)")
        return holdings
    except FileNotFoundError:
        print("    portfolio.json not found — no portfolio loaded")
        return []
    except json.JSONDecodeError as e:
        print(f"    Error reading portfolio.json: {e}")
        return []
