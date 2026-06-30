set dotenv-load := true

generate:
    uv run --env-file .env generate_report.py

deploy:
    rsync -avz generate_report.py render-charts.js ignore.txt $SERVER:~/opt/dnsreport

first_deploy:
    rsync -avz .env run.sh $SERVER:~/opt/dnsreport
    just deploy
