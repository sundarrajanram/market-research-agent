"""Scrape Motley Fool recommendations (requires subscription login)."""
import requests
from bs4 import BeautifulSoup


class MotleyFoolScraper:
    BASE_URL = "https://www.fool.com"
    LOGIN_URL = "https://www.fool.com/auth/authenticate"

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
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
