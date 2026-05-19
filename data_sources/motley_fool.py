"""Scrape Motley Fool recommendations and portfolio (requires subscription login)."""
import requests
from bs4 import BeautifulSoup
import re


class MotleyFoolScraper:
    BASE_URL = "https://www.fool.com"
    LOGIN_URL = "https://www.fool.com/auth/authenticate"

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        self.logged_in = False

    def login(self):
        """Log in to Motley Fool."""
        try:
            login_page = self.session.get(f"{self.BASE_URL}/auth/login", timeout=15)
            soup = BeautifulSoup(login_page.text, "html.parser")

            csrf = None
            csrf_input = soup.find("input", {"name": "_token"})
            if csrf_input:
                csrf = csrf_input.get("value")

            payload = {
                "email": self.email,
                "password": self.password,
            }
            if csrf:
                payload["_token"] = csrf

            resp = self.session.post(self.LOGIN_URL, data=payload, timeout=15)
            self.logged_in = resp.status_code == 200
            return self.logged_in
        except Exception as e:
            print(f"Motley Fool login error: {e}")
            return False

    def get_portfolio(self, portfolio_name="My Robinhood Stock"):
        """Get stocks from a user's custom portfolio."""
        if not self.logged_in:
            self.login()

        holdings = []
        try:
            # Try portfolio pages
            urls = [
                f"{self.BASE_URL}/portfolios/",
                f"{self.BASE_URL}/premium/portfolios/",
                f"{self.BASE_URL}/my-fool/portfolios/",
            ]
            for url in urls:
                resp = self.session.get(url, timeout=15)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")

                # Find the specific portfolio by name
                portfolio_link = soup.find("a", string=re.compile(portfolio_name, re.IGNORECASE))
                if not portfolio_link:
                    portfolio_link = soup.find(string=re.compile(portfolio_name, re.IGNORECASE))
                    if portfolio_link:
                        portfolio_link = portfolio_link.find_parent("a")

                if portfolio_link:
                    href = portfolio_link.get("href", "")
                    if href and not href.startswith("http"):
                        href = self.BASE_URL + href
                    if href:
                        portfolio_resp = self.session.get(href, timeout=15)
                        if portfolio_resp.status_code == 200:
                            holdings = self._parse_portfolio_page(portfolio_resp.text)
                            if holdings:
                                break

                # If no direct link, try parsing the page for stock rows
                if not holdings:
                    holdings = self._parse_portfolio_page(resp.text)
                    if holdings:
                        break

        except Exception as e:
            print(f"Error fetching portfolio: {e}")
        return holdings

    def _parse_portfolio_page(self, html):
        """Parse a portfolio page for stock holdings."""
        holdings = []
        soup = BeautifulSoup(html, "html.parser")

        # Look for table rows with stock data
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows[1:]:  # Skip header
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    symbol_cell = cells[0]
                    symbol = symbol_cell.get_text(strip=True).upper()
                    # Filter out non-ticker text
                    if re.match(r'^[A-Z]{1,5}$', symbol):
                        holding = {"symbol": symbol}
                        if len(cells) >= 3:
                            try:
                                holding["shares"] = float(re.sub(r'[^\d.]', '', cells[1].get_text(strip=True)) or 0)
                            except (ValueError, IndexError):
                                holding["shares"] = 0
                        if len(cells) >= 4:
                            try:
                                holding["cost_basis"] = float(re.sub(r'[^\d.]', '', cells[2].get_text(strip=True)) or 0)
                            except (ValueError, IndexError):
                                holding["cost_basis"] = 0
                        holdings.append(holding)

        # Also try div-based layouts
        if not holdings:
            stock_items = soup.find_all("div", {"data-symbol": True})
            for item in stock_items:
                symbol = item.get("data-symbol", "").upper()
                if symbol:
                    holdings.append({"symbol": symbol, "shares": 0, "cost_basis": 0})

        # Try finding ticker symbols in links
        if not holdings:
            ticker_links = soup.find_all("a", href=re.compile(r'/quote/[A-Z]+'))
            seen = set()
            for link in ticker_links:
                match = re.search(r'/quote/([A-Z]+)', link.get("href", ""))
                if match:
                    symbol = match.group(1)
                    if symbol not in seen:
                        seen.add(symbol)
                        holdings.append({"symbol": symbol, "shares": 0, "cost_basis": 0})

        return holdings

    def get_stock_advisor_picks(self):
        """Get latest Stock Advisor recommendations."""
        if not self.logged_in:
            self.login()

        picks = []
        try:
            urls = [
                f"{self.BASE_URL}/premium/stock-advisor/recommendations/",
                f"{self.BASE_URL}/premium/stock-advisor/",
            ]
            for url in urls:
                resp = self.session.get(url, timeout=15)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    recs = soup.find_all("div", class_="recommendation")
                    if not recs:
                        recs = soup.find_all("article")

                    for rec in recs[:10]:
                        title = rec.find(["h2", "h3", "a"])
                        if title:
                            picks.append({
                                "title": title.get_text(strip=True),
                                "link": title.get("href", ""),
                                "source": "Stock Advisor",
                            })
                    if picks:
                        break
        except Exception as e:
            print(f"Error fetching Stock Advisor: {e}")
        return picks

    def get_rule_breakers_picks(self):
        """Get latest Rule Breakers recommendations."""
        if not self.logged_in:
            self.login()

        picks = []
        try:
            url = f"{self.BASE_URL}/premium/rule-breakers/recommendations/"
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                recs = soup.find_all("div", class_="recommendation")
                if not recs:
                    recs = soup.find_all("article")

                for rec in recs[:10]:
                    title = rec.find(["h2", "h3", "a"])
                    if title:
                        picks.append({
                            "title": title.get_text(strip=True),
                            "link": title.get("href", ""),
                            "source": "Rule Breakers",
                        })
        except Exception as e:
            print(f"Error fetching Rule Breakers: {e}")
        return picks

    def get_free_articles(self):
        """Get latest free Motley Fool articles for sentiment."""
        articles = []
        try:
            resp = self.session.get(f"{self.BASE_URL}/investing-news/", timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                links = soup.find_all("a", class_="text-gray-1100")
                if not links:
                    links = soup.select("h4 a, h3 a")

                for link in links[:15]:
                    articles.append({
                        "title": link.get_text(strip=True),
                        "link": self.BASE_URL + link.get("href", ""),
                        "source": "Motley Fool",
                    })
        except Exception as e:
            print(f"Error fetching Fool articles: {e}")
        return articles
