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
import requests
import openai

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
import os
import tweepy

now = time.time()

# Tweet

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
    text="Can't get enough cybersecurity news? Add https://cyberfeed.io/feed to your RSS reader today!"
)

# Toot

from mastodon import Mastodon

m = Mastodon(
    access_token=os.environ["TOOT_TOKEN"],
    api_base_url="https://mstdn.social",
)

m.toot(
    "Can't get enough cybersecurity news? Add https://cyberfeed.io/feed to your RSS reader today!"
)
