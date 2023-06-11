from datetime import datetime, timedelta
from mastodon import Mastodon
import operator
import re
import sqlite3
import os


def get_db_connection():
    conn = sqlite3.connect("/app/rss.db")
    conn.row_factory = sqlite3.Row
    return conn


#  Set up access
instance = "https://mstdn.social"
mastodon = Mastodon(api_base_url=instance, access_token=os.environ["TOOT_TOKEN"])

#  Get user's info
me = mastodon.me()
my_id = me["id"]
year_joined = me["created_at"].year

#  Today's date

toots = []

for day in range(1, 8):

    day_time = datetime.now() - timedelta(days=day)

    #  Bitwise shift the integer representation and convert to milliseconds
    min_id = (int(day_time.timestamp()) << 16) * 1000

    #  Call the API
    statuses = mastodon.account_statuses(
        id=my_id, min_id=min_id, limit="40", exclude_reblogs=True
    )

    #  Print the statuses

    for status in statuses:

        #  Add to the list of toots
        toots.append(status)

# Calculate a score for each toot (boosts + replies + favorites)
toot_scores = {}

for toot in toots:

    score = (
        int(toot["reblogs_count"])
        + int(toot["replies_count"])
        + int(toot["favourites_count"])
    )

    url_regex = r'https?://[^\s<>"\']+'  # regex to match http or https URLs
    match = re.search(url_regex, toot["content"])

    if match:
        url = match.group()

        id_regex = r"article/([a-z0-9]+)"
        match = re.search(id_regex, url)

        if match:
            id = match.group(
                1
            )  # group(1) to get the content of the first (and only) group

    # Add everything to the dictionary
    toot_scores[toot["content"], toot["id"], toot["uri"], url, id] = score

# Sort the dictionary by score
sorted_toots = sorted(toot_scores.items(), key=operator.itemgetter(1), reverse=True)

# Update database with the top 5 toots

with get_db_connection() as conn:

    cur = conn.cursor()

    for toot in sorted_toots[:6]:

        # Check if the article is already in the database/top table
        article_link_hash_check = cur.execute(
            "SELECT article_link_hash FROM top WHERE article_link_hash=?", [toot[0][4]]
        )
        article_link_hash_check = article_link_hash_check.fetchone()

        if not article_link_hash_check:

            article_title_search = cur.execute(
                "SELECT article_title FROM rss WHERE article_link_hash=?", [toot[0][4]]
            )
            article_title = article_title_search.fetchone()

            article_date_published_epoch = cur.execute(
                "SELECT article_date_published_epoch FROM rss WHERE article_link_hash=?",
                [toot[0][4]],
            )
            article_date_published_epoch = article_date_published_epoch.fetchone()

            cur.execute(
                "INSERT INTO top (article_title, cf_id, mastodon_uri, cf_url, article_link_hash, score, article_date_published_epoch) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    article_title[0],
                    toot[0][1],
                    toot[0][2],
                    toot[0][3],
                    toot[0][4],
                    toot[1],
                    article_date_published_epoch[0],
                ],
            )
            conn.commit()
