#!/bin/bash
# Daily market research runner
cd /home/ramalisu/.workspace/market-research-agent
/home/ramalisu/.workspace/market-research-agent/venv/bin/python main.py >> /home/ramalisu/.workspace/market-research-agent/logs/cron.log 2>&1
