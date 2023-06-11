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


from mastodon import Mastodon

m = Mastodon(
    access_token=os.environ["TOOT_TOKEN"],
    api_base_url="https://mstdn.social",
)

# Search for the account using its username (replace 'username' with the actual username)

username_list = [
    "@BleepingComputer@infosec.exchange",
    "@campuscodi@mastodon.social",
    "@SwiftOnSecurity@infosec.exchange",
    "@alyssam_infosec@infosec.exchange",
    "@racheltobac@infosec.exchange",
]

for user in username_list:

    username = user
    accounts = m.account_search(username)

    # Check if the account was found
    if accounts:
        # Get the account ID
        account_id = accounts[0]["id"]

        # Get the toots of the account
        toots = m.account_statuses(account_id)

        # Check if there are any toots
        if toots:
            # Get the newest toot
            newest_toot = toots[0]

            # Get the ID of the newest toot
            toot_id = newest_toot["id"]

            # Retoot (boost) the newest toot
            m.status_reblog(toot_id)
            print("Successfully retooted the newest toot!")
        else:
            print("The account has no toots.")
    else:
        print("Account not found.")
