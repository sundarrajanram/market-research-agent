"""Send report via email."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import config


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


def save_report_to_file(html_content):
    """Fallback: save report as HTML file."""
    import os
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/report_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    with open(filename, "w") as f:
        f.write(html_content)
    print(f"Report saved to {filename}")
