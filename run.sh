#!/bin/bash
cd /home/me/opt/dnsreport
/usr/local/bin/uv run --env-file .env generate_report.py
