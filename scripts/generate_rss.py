import hashlib
import feedparser
from io import StringIO
from html.parser import HTMLParser
import sqlite3
import calendar
from datetime import datetime
from feedgen.feed import FeedGenerator
import time
import json
import sys
import logging

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def get_db_connection():
    conn = sqlite3.connect("/app/rss.db")
    conn.execute("pragma journal_mode=wal")
    conn.row_factory = sqlite3.Row
    return conn


def add_to_rss(now):
    with get_db_connection() as conn:
        news = conn.execute(
            f"SELECT * FROM rss WHERE article_date_published_epoch >= ({now} - 86400) ORDER BY article_date_published DESC"
        ).fetchall()

        fg = FeedGenerator()
        fg.title("Cyberfeed.io")
        fg.description("Daily Cybersecurity News")
        fg.link(href="https://cyberfeed.io")
        fg.id("https://cyberfeed.io")
        fg.author({"name": "Andrew Katz", "email": "andrew@akatz.org"})
        fg.link(href="https://cyberfeed.io/feed", rel="alternate")
        fg.language("en")

        for article in news:
            if article[1] > (now - 86400):
                fe = fg.add_entry()
                fe.title(article[2])
                fe.link(href=article[3])
                fe.description(article[5])
                fe.pubDate(
                    datetime.fromtimestamp(article[1]).strftime(
                        "%Y-%m-%dT%H:%M:%S+00:00"
                    )
                )
                fe.enclosure(url=article[6], type="image/jpeg", length=0)

    fg.rss_file("/app/templates/rss.xml")


if __name__ == "__main__":
    now = time.time()
    add_to_rss(now)
