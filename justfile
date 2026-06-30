set dotenv-load := true

generate:
    uv run --env-file .env generate_report.py

deploy:
    rsync -avz --ignore-existing .env run.sh $SERVER:~/opt/steamhours
    rsync -avz compute_steam_hours.py $SERVER:~/opt/steamhours
