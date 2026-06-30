set dotenv-load := true

generate:
    uv run --env-file .env generate_report.py

deploy:
    rsync -avz --ignore-existing .env run.sh $SERVER:~/opt/dnsreport
    rsync -avz generate_report.py render-charts.js ignore.txt $SERVER:~/opt/dnsreport
