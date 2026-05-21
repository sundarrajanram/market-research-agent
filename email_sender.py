"""Send report via email."""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import config

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")


def send_report(html_content):
    """Send HTML report via email."""
    if not config.SMTP_PASSWORD or config.SMTP_PASSWORD == "your_gmail_app_password_here":
        print("SMTP not configured. Saving report to file instead.")
        save_report_to_file(html_content)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Market Intelligence Report - {datetime.now().strftime('%B %d, %Y')}"
    msg["From"] = config.SMTP_EMAIL
    msg["To"] = config.RECIPIENT_EMAIL

    plain_text = "Please view this email in an HTML-capable email client."
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_EMAIL, config.SMTP_PASSWORD)
        server.sendmail(config.SMTP_EMAIL, config.RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        print(f"Report sent to {config.RECIPIENT_EMAIL}")
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        save_report_to_file(html_content)
        return False


def send_market_open_report(html_content):
    """Send market open flash report via email."""
    if not config.SMTP_PASSWORD or config.SMTP_PASSWORD == "your_gmail_app_password_here":
        print("SMTP not configured. Saving market open report to file instead.")
        save_report_to_file(html_content, prefix="market_open")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Market Open Flash - {datetime.now().strftime('%B %d, %Y')}"
    msg["From"] = config.SMTP_EMAIL
    msg["To"] = config.RECIPIENT_EMAIL

    plain_text = "Please view this email in an HTML-capable email client."
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_EMAIL, config.SMTP_PASSWORD)
        server.sendmail(config.SMTP_EMAIL, config.RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        print(f"Market open report sent to {config.RECIPIENT_EMAIL}")
        return True
    except Exception as e:
        print(f"Market open email send failed: {e}")
        save_report_to_file(html_content, prefix="market_open")
        return False


def send_eod_report(html_content):
    """Send EOD flash report via email."""
    if not config.SMTP_PASSWORD or config.SMTP_PASSWORD == "your_gmail_app_password_here":
        print("SMTP not configured. Saving EOD report to file instead.")
        save_report_to_file(html_content, prefix="eod_flash")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"EOD Portfolio Flash - {datetime.now().strftime('%B %d, %Y')}"
    msg["From"] = config.SMTP_EMAIL
    msg["To"] = config.RECIPIENT_EMAIL

    plain_text = "Please view this email in an HTML-capable email client."
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_EMAIL, config.SMTP_PASSWORD)
        server.sendmail(config.SMTP_EMAIL, config.RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        print(f"EOD flash report sent to {config.RECIPIENT_EMAIL}")
        return True
    except Exception as e:
        print(f"EOD flash email send failed: {e}")
        save_report_to_file(html_content, prefix="eod_flash")
        return False


def save_report_to_file(html_content, prefix="report"):
    """Fallback: save report as HTML file."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    filename = os.path.join(REPORTS_DIR, f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M')}.html")
    with open(filename, "w") as f:
        f.write(html_content)
    print(f"Report saved to {filename}")
