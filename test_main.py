import main
from fastapi.testclient import TestClient
import pytest
import sqlite3


client = TestClient(main.app)


@pytest.fixture
def setup_database():
    """Fixture to set up the in-memory database with test data"""
    conn = sqlite3.connect("/app/rss.db")
    cursor = conn.cursor()
    cursor.execute(
        """
	    CREATE TABLE rss
        (article_date_published,article_date_published_epoch,article_title,article_link,article_link_hash,article_shortdesc,article_image,article_hnlink)
        """
    )
    cursor.execute(
        """
        CREATE TABLE stocks
        (percentage, status, stock_name)
        """
    )
    cursor.execute(
        """
        CREATE TABLE top
        (article_title,cf_id,mastodon_url,cf_url,article_link_hash,score,article_date_published_epoch)
        """
    )
    rss_sample_data = [
        (
            "2023-01-01",
            1669765297,
            "Sample Article Name",
            "https://cyberfeed.io/article/9c09b163e879476443d8f08bbfbec1c9",
            "0843353daa63879a84c3dae4d07b23b5",
            "Sample Short Description",
            "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png",
            "https://news.ycombinator.com/item?id=123456",
        )
    ]
    stocks_sample_data = [("2.00", "green", "JAMF")]
    top_sample_data = [
        (
            "Sample Article Name",
            "9c09b163e879476443d8f08bbfbec1c9",
            "https://mstdn.social/users/cyberfeed/statuses/110267202302766680",
            "https://cyberfeed.io/article/9c09b163e879476443d8f08bbfbec1c9",
            "0843353daa63879a84c3dae4d07b23b5",
            1,
            1669765297,
        )
    ]
    cursor.executemany(
        "INSERT INTO rss VALUES(?, ?, ?, ?, ?, ?, ?, ?)", rss_sample_data
    )
    cursor.executemany("INSERT INTO stocks VALUES(?, ?, ?)", stocks_sample_data)
    conn.commit()
    yield conn


def test_read_index(setup_database):
    response = client.get("/")
    assert response.status_code == 200
    assert (
        "<title>Cyberfeed.io | Daily Cybersecurity News and Insights</title>"
        in response.text
    )


def test_read_article():
    response = client.get("/article/0843353daa63879a84c3dae4d07b23b5")
    assert response.status_code == 200
    assert "<title>Sample Article Name | Cyberfeed.io</title>" in response.text
    assert "Sample Short Description" in response.text
    assert "Sample Article Name" in response.text
    assert (
        "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"
        in response.text
    )
    assert (
        "https://cyberfeed.io/article/9c09b163e879476443d8f08bbfbec1c9" in response.text
    )


def test_read_feed():
    response = client.get("/feed")
    assert response.status_code == 200


def test_read_robots_txt():
    response = client.get("/robots.txt")
    assert response.status_code == 200


def test_read_404_page():
    response = client.get("/404")
    assert response.status_code == 200
