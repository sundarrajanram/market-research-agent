"""Load portfolio from Robinhood via Snaptrade API."""
import os
from snaptrade_client import SnapTrade


def load_portfolio_from_snaptrade():
    """Pull current holdings from Robinhood via Snaptrade."""
    client_id = os.getenv("SNAPTRADE_CLIENT_ID")
    consumer_key = os.getenv("SNAPTRADE_CONSUMER_KEY")
    user_id = os.getenv("SNAPTRADE_USER_ID")
    user_secret = os.getenv("SNAPTRADE_USER_SECRET")

    if not all([client_id, consumer_key, user_id, user_secret]):
        return None

    try:
        snaptrade = SnapTrade(
            consumer_key=consumer_key,
            client_id=client_id,
        )

        # Get accounts
        accounts = snaptrade.account_information.list_user_accounts(
            user_id=user_id,
            user_secret=user_secret,
        )

        # Find the Individual (non-crypto) account
        account_id = None
        for account in accounts.body:
            if account.get("meta", {}).get("type") != "DIGITALASSET":
                account_id = account["id"]
                break

        if not account_id:
            print("    No investment account found in Snaptrade")
            return None

        # Get positions
        positions = snaptrade.account_information.get_user_account_positions(
            user_id=user_id,
            user_secret=user_secret,
            account_id=account_id,
        )

        holdings = []
        for pos in positions.body:
            symbol = pos["symbol"]["symbol"]["symbol"]
            units = pos.get("units", 0)
            if units and float(units) > 0:
                # Snaptrade uses MOG.A format, yfinance uses MOG-A
                symbol = symbol.replace(".", "-")
                holdings.append({
                    "symbol": symbol,
                    "shares": float(units),
                })

        return holdings

    except Exception as e:
        print(f"    Snaptrade error: {e}")
        return None
