"""Schedule daily report at 5 AM PST."""
import schedule
import time
import os
from datetime import datetime
from main import run_research


def job():
    """Run the daily research job."""
    print(f"\n{'='*60}")
    print(f"  SCHEDULED RUN: {datetime.now()}")
    print(f"{'='*60}\n")
    try:
        run_research()
    except Exception as e:
        print(f"ERROR in scheduled run: {e}")


if __name__ == "__main__":
    os.environ["TZ"] = "America/Los_Angeles"
    try:
        time.tzset()
    except AttributeError:
        pass

    schedule.every().day.at("05:00").do(job)

    print(f"Market Research Agent started.")
    print(f"Scheduled to run daily at 5:00 AM PST.")
    print(f"Current time (PST): {datetime.now()}")
    print(f"Press Ctrl+C to stop.\n")

    # Run immediately on first start for testing
    print("Running initial report now...")
    job()

    while True:
        schedule.run_pending()
        time.sleep(60)
