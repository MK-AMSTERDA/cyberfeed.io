import hashlib
import feedparser
from io import StringIO
from html.parser import HTMLParser
import sqlite3
import calendar
from datetime import datetime
import time
import sys
import logging
import os
import tweepy
import requests
import openai

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

now = time.time()


def get_db_connection():
    conn = sqlite3.connect("/app/rss.db")
    conn.execute("pragma journal_mode=wal")
    conn.row_factory = sqlite3.Row
    return conn


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d):
        self.text.write(d)

    def get_data(self):
        return self.text.getvalue()


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


# List of URLs to parse
urls = ["https://hnrss.org/frontpage?points=400"]
feeds = [feedparser.parse(url)["entries"] for url in urls]
feed = [item for feed in feeds for item in feed]

# Open up the database
with get_db_connection() as conn:
    for i in feed:
        # Create an MD5 Hash of the article_title
        article_link_hash_check = hashlib.md5(i["link"].encode("UTF-8")).hexdigest()

        # See if article_title is anywhere in the database
        cur = conn.cursor()
        cur.execute(
            "SELECT article_link_hash FROM rss WHERE article_link_hash=?",
            (article_link_hash_check,),
        )
        result = cur.fetchone()

        # If there is no result, insert the article title, link, and MD5 hash into the database
        if not result:
            # Formatting, Dateparsing, & Cleaning :O)
            epoch_time = calendar.timegm(i["published_parsed"])
            date = datetime.fromtimestamp(epoch_time).strftime("%Y-%m-%d %H:%M:%S")
            # Strips all HTML from short_desc
            description = strip_tags(
                i["description"]
                .replace("N/A", "")
                .replace("\n", " ")
                .replace("\xa0", " ")
                .replace("...", "")
                .replace(
                    "This is UL Member Content Subscribe Already a member? Login", ""
                )
            )

            title = i["title"]

            LINK_PREVIEW_KEY = os.environ["LINK_PREVIEW_KEY"]

            url = f"http://api.linkpreview.net/?key={LINK_PREVIEW_KEY}&q=" + i["link"]

            link_prev = requests.get(url).json()

            # OpenAI enrichment

            if len(title) < 50:
                ai_description = "A new thread was posted on HN. Check it out!"

            else:

                description_for_ai = title
                OPENAI_SECRET = os.environ["OPENAI_SECRET"]
                openai.api_key = OPENAI_SECRET

                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "user",
                            "content": f"Rephrase this text in a short news paragraph: '{description_for_ai}'.",
                        }
                    ],
                )

                ai_description = completion["choices"][0]["message"]["content"].lstrip()

            # Add the info to the database
            cur.execute(
                "INSERT INTO rss (article_date_published,article_date_published_epoch,article_title,article_link,article_link_hash,article_shortdesc,article_image,article_hnlink) VALUES (?,?,?,?,?,?,?,?)",
                (
                    date,
                    epoch_time,
                    title,
                    i["link"],
                    article_link_hash_check,
                    ai_description,
                    link_prev["image"],
                    i["comments"],
                ),
            )
            conn.commit()

            # Tweet

            hashtags = " #tech #security #infosec #cybersecurity"

            CONSUMER_KEY = os.environ["CONSUMER_KEY"]
            CONSUMER_SECRET = os.environ["CONSUMER_SECRET"]
            ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
            ACCESS_TOKEN_SECRET = os.environ["ACCESS_TOKEN_SECRET"]

            client = tweepy.Client(
                consumer_key=CONSUMER_KEY,
                consumer_secret=CONSUMER_SECRET,
                access_token=ACCESS_TOKEN,
                access_token_secret=ACCESS_TOKEN_SECRET,
            )

            client.create_tweet(
                text=title
                + " https://cyberfeed.io/article/"
                + article_link_hash_check
                + hashtags
            )

            # Toot

            from mastodon import Mastodon

            m = Mastodon(
                access_token=os.environ["TOOT_TOKEN"],
                api_base_url="https://mstdn.social",
            )

            m.toot(
                title
                + " https://cyberfeed.io/article/"
                + article_link_hash_check
                + hashtags
            )
