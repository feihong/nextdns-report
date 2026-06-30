# NextDNS Report

## Example .env file

```
API_KEY=abcde
PROFILE_ID=abcde
OUTPUT_FILE=/home/me/public_html/dnsreport/index.html
TIMEZONE='America/Chicago'

SERVER=myserver.com

```

## Tables

```
CREATE TABLE IF NOT EXISTS log (
    timestamp TEXT,
    domain    TEXT,
    UNIQUE(timestamp, domain)
);
```

## Set up cron job

1. Create `~/opt/dnsreport/.env` on your server
1. `just deploy`
1. `chmod u+v ~/opt/dnsreport/run.sh`
1. Edit the `OUTPUT_FILE` value inside `.env` to generate your report inside a published web directory
1. `crontab -e`
1. Add line `@hourly /home/me/opt/dnsreport/run.sh`
1. `crontab -l` to see your jobs
