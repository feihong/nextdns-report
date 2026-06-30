#!/bin/bash
cd /home/me/opt/dnsreport
/usr/local/bin/uv run --env-file .env generate_report.py

export $(cat .env | xargs)
cp render-charts.js $OUTPUT_DIR
