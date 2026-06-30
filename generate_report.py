# /// script
# requires-python = ">=3.13"
# dependencies = ["requests", "htpy"]
# ///

import os
import json
import sqlite3
import csv
import subprocess
import datetime
from pathlib import Path
import re
import itertools
from zoneinfo import ZoneInfo
import html

import requests
from htpy import (html, head, meta, title, style, body, h1, h2, table, thead, tbody, tr, th, td, a as anchor, script)
from markupsafe import Markup


API_KEY = os.environ['API_KEY']
PROFILE_ID = os.environ['PROFILE_ID']
OUTPUT_FILE = Path(os.environ['OUTPUT_DIR']) / 'index.html'
TIMEZONE = os.environ['TIMEZONE']


STYLES = """
table {
  border-collapse: collapse;
}
th, td {
  border: 1px solid #777;
  padding: 1em;
}
"""


here = Path(__file__).parent
log_file = here / 'log.csv'
ignore_file = Path(here / 'ignore.txt')
script_file = Path(here / 'render-charts.js')
my_tz = ZoneInfo(TIMEZONE)
con = sqlite3.connect(here / 'database.sqlite', autocommit=True)
cur = con.cursor()


class Blacklist:
    ignore_re = None

    @staticmethod
    def setup():
        def generate():
            for line in ignore_file.read_text().splitlines():
                line = line.strip()
                if line:
                    yield line.replace('.', '[.]').replace('*', '.+')

        regex = '|'.join(generate())
        # import pdb; pdb.set_trace()
        Blacklist.ignore_re = re.compile(regex)

    @staticmethod
    def should_ignore(domain):
        return Blacklist.ignore_re.match(domain)


def main():
    setup()
    download()
    update()
    domain_stats = get_domain_stats()
    time_stats = get_time_stats()
    generate_report(domain_stats, time_stats)
    cleanup()


def download():
    url = f'https://api.nextdns.io/profiles/{PROFILE_ID}/logs/download'
    cmd = [
        'curl',
        '-L', # follow redirects
        '-H', f'X-Api-Key: {API_KEY}',
        url,
        '-o',
        log_file
    ]
    subprocess.run(cmd)


def setup():
    cur.execute('''
    CREATE TABLE IF NOT EXISTS log (
        timestamp TEXT,
        domain    TEXT,
        UNIQUE(timestamp, domain)
    );
    ''')
    Blacklist.setup()


def update():
    def get_rows(reader):
        for row in reader:
            domain = row['root_domain']
            # Convert to my preferred timezone
            dt = datetime.datetime.fromisoformat(row['timestamp']).astimezone(my_tz)
            if not Blacklist.should_ignore(domain):
                yield dt.strftime('%Y-%m-%d %H:%M:%S.%f'), domain

    with log_file.open('r') as fp:
        reader = csv.DictReader(fp)
        con.executemany('''
        INSERT INTO log (timestamp, domain) VALUES (?, ?)
        ON CONFLICT (timestamp, domain) DO NOTHING;
        ''', get_rows(reader))


def get_domain_stats():
    """
    Get number of requests for a given domain on a given day
    """
    cur.execute('''
    SELECT  date(timestamp) as day, domain, count(*) as count
    FROM log
    GROUP BY day, domain
    ORDER BY day DESC, count DESC
    ''')
    return itertools.groupby(cur.fetchall(), lambda r: r[0])


def get_time_stats():
    """
    Get number of requests for a given hour of a day
    """
    cur.execute('''
    SELECT strftime('%Y-%m-%d %H:00', timestamp) as hour_of_day, count(*)
    FROM log
    GROUP BY hour_of_day
    ORDER BY hour_of_day DESC
    ''')
    return itertools.groupby(cur.fetchall(), lambda r: r[0][:10])


def layout(content):
    title_text = 'NextDNS Traffic Report'

    return html[
        head[
            meta(charset='utf-8'),
            meta(name='viewport', content='width=device-width,initial-scale=1'),
            title[title_text],
            style[STYLES],
            script(src='https://cdn.plot.ly/plotly-3.6.0.min.js'),
        ],
        body[
            h1[title_text],
            *content,
            script(src='render-charts.js'),
        ]
    ]


def generate_report(domain_stats, time_stats):
    def get_stats():
        for (date1, ds), (date2, ts) in zip(domain_stats, time_stats):
            assert date1 == date2
            yield date1, ds, ts

    def row(line):
        _, domain, count = line
        return tr[
            td[
                anchor(target='_blank', href='https://google.com/search?q=' + domain)[domain]
            ],
            td[count],
        ]

    def histogram_data(time_lines):
        def generate():
            for hour_of_day, count in time_lines:
                yield hour_of_day[11:], count

        lst = list(generate())
        lst.sort(key=lambda x: x[0])
        return Markup(json.dumps(lst))

    def content():
        for date, domain_lines, time_lines in get_stats():
            yield h2[date]

            yield table[
                thead[
                    tr[th['Domain'], th['Count']]
                ],
                tbody[
                    [row(line) for line in domain_lines]
                ]
            ]

            yield script(class_='histogram', type='application/json')[
                histogram_data(time_lines)
            ]


    with open(OUTPUT_FILE, 'w') as fp:
        fp.write(str(layout(content())))

    print(f'Generated report to {OUTPUT_FILE}')


def cleanup():
    # Delete log rows older than two weeks
    now = datetime.datetime.today() - datetime.timedelta(days=14)
    cur.execute('DELETE FROM log WHERE timestamp < ?', (now.timestamp(),))


if __name__ == '__main__':
    main()
