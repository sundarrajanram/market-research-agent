"""Read Robinhood portfolio (read-only)."""
import robin_stocks.robinhood as rh


class RobinhoodReader:
    def __init__(self, email, password, mfa_code=None, totp_secret=None):
        self.email = email
        self.password = password
        self.mfa_code = mfa_code
        self.totp_secret = totp_secret
        self.logged_in = False

    def login(self):
        """Log in to Robinhood. Handles MFA if totp_secret is provided."""
        try:
            if self.totp_secret:
                import pyotp
                totp = pyotp.TOTP(self.totp_secret)
                self.mfa_code = totp.now()

            login_kwargs = {
                "username": self.email,
                "password": self.password,
                "store_session": True,
            }
            if self.mfa_code:
                login_kwargs["mfa_code"] = self.mfa_code

            rh.login(**login_kwargs)
            self.logged_in = True
            return True
        except Exception as e:
            print(f"Robinhood login error: {e}")
            return False

    def get_portfolio_summary(self):
        """Get overall portfolio value and daily change."""
        if not self.logged_in:
            return None
        try:
            profile = rh.profiles.load_portfolio_profile()
            return {
                "equity": float(profile.get("equity", 0)),
                "extended_hours_equity": float(profile.get("extended_hours_equity") or profile.get("equity", 0)),
                "market_value": float(profile.get("market_value", 0)),
                "total_gain": float(profile.get("equity", 0)) - float(profile.get("total_deposited", 0) or 0),
            }
        except Exception as e:
            print(f"Error fetching portfolio summary: {e}")
            return None

    def get_holdings(self):
        """Get current stock holdings with cost basis and performance."""
        if not self.logged_in:
            return []
        try:
            holdings = rh.account.build_holdings()
            result = []
            for symbol, data in holdings.items():
                result.append({
                    "symbol": symbol,
                    "name": data.get("name", symbol),
                    "quantity": float(data.get("quantity", 0)),
                    "avg_cost": float(data.get("average_buy_price", 0)),
                    "current_price": float(data.get("price", 0)),
                    "equity": float(data.get("equity", 0)),
                    "percent_change": float(data.get("percent_change", 0)),
                    "total_return_pct": float(data.get("percentage", 0)),
                    "type": data.get("type", "stock"),
                })
            result.sort(key=lambda x: x["equity"], reverse=True)
            return result
        except Exception as e:
            print(f"Error fetching holdings: {e}")
            return []

    def get_portfolio_allocation(self, holdings):
        """Calculate sector/position allocation from holdings."""
        total_equity = sum(h["equity"] for h in holdings)
        if total_equity == 0:
            return {}

        allocation = {}
        for h in holdings:
            pct = round(h["equity"] / total_equity * 100, 1)
            allocation[h["symbol"]] = {
                "percent": pct,
                "equity": h["equity"],
                "return_pct": h["total_return_pct"],
            }
        return allocation

    def get_watchlist(self):
        """Get user's Robinhood watchlist."""
        if not self.logged_in:
            return []
        try:
            watchlist = rh.account.get_watchlist_by_name()
            symbols = []
            if watchlist and "results" in watchlist:
                for item in watchlist["results"]:
                    instrument_url = item.get("instrument")
                    if instrument_url:
                        instrument = rh.helper.request_get(instrument_url)
                        if instrument:
                            symbols.append(instrument.get("symbol"))
            return symbols
        except Exception as e:
            print(f"Error fetching watchlist: {e}")
            return []

    def get_recent_orders(self, days=7):
        """Get recent buy/sell orders."""
        if not self.logged_in:
            return []
        try:
            orders = rh.orders.get_all_stock_orders()
            recent = []
            for order in orders[:20]:
                if order.get("state") == "filled":
                    recent.append({
                        "symbol": order.get("symbol", ""),
                        "side": order.get("side", ""),
                        "quantity": order.get("quantity", ""),
                        "price": order.get("average_price", ""),
                        "date": order.get("last_transaction_at", ""),
                    })
            return recent
        except Exception as e:
            print(f"Error fetching orders: {e}")
            return []

    def logout(self):
        """Log out of Robinhood."""
        try:
            rh.logout()
        except Exception:
            pass
