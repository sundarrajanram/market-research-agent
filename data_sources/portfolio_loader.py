"""Load portfolio from local JSON file or GitHub repo."""
import json
import os
import requests


def load_portfolio(filepath=None):
    """Load portfolio holdings. Tries GitHub raw file first, then local."""
    # Try loading from GitHub (so you can edit from phone/browser)
    github_url = os.getenv("PORTFOLIO_URL")
    if github_url:
        try:
            resp = requests.get(github_url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("holdings", [])
        except Exception as e:
            print(f"  Could not fetch portfolio from GitHub: {e}")

    # Fall back to local file
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
