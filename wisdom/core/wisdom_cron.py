"""
Wisdom Cron — Scheduler don gian chay bang Python
Thay cho Task Scheduler Windows hoac crontab Unix.

Usage:
    python wisdom_cron.py          # Chay daemon (background)
    python wisdom_cron.py --test   # Test chay report ngay bay gio

Schedule mac dinh:
    Thu 2 luc 07:00 -> Weekly report
    Hang ngay 20:00 -> Decay cleanup (neu co wisdom_decay.py)
"""

import time
import argparse
import subprocess
import sys
import os
from datetime import datetime

PYTHON = sys.executable
BASE   = os.path.dirname(os.path.abspath(__file__))

def run_report():
    print(f"[{datetime.now().strftime('%H:%M %d/%m')}] Running weekly report...")
    subprocess.run([PYTHON, os.path.join(BASE, "wisdom_report.py"), "--days", "7"])

def should_run_report() -> bool:
    now = datetime.now()
    return now.weekday() == 0 and now.hour == 7 and now.minute < 5

def run_daemon():
    print("Wisdom Cron started. Ctrl+C to stop.")
    print("Schedule: Monday 07:00 -> weekly report")
    last_report_day = -1
    while True:
        now = datetime.now()
        if should_run_report() and now.day != last_report_day:
            run_report()
            last_report_day = now.day
        time.sleep(60)  # Check moi phut

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Test: chay report ngay bay gio")
    args = parser.parse_args()

    if args.test:
        run_report()
    else:
        run_daemon()
