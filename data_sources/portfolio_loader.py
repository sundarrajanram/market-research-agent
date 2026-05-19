"""Load portfolio from local JSON file."""
import json
import os


def load_portfolio(filepath=None):
    """Load portfolio holdings from portfolio.json."""
    if filepath is None:
        filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "portfolio.json")

    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        return data.get("holdings", [])
    except FileNotFoundError:
        print("  portfolio.json not found — no portfolio loaded")
        return []
    except json.JSONDecodeError as e:
        print(f"  Error reading portfolio.json: {e}")
        return []
