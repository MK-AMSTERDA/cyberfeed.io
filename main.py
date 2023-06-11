import os
import time
import requests
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
import sqlite3

GOAT_SECRET = os.environ["GOAT_SECRET"]

app = FastAPI()

app.mount("/app/static", StaticFiles(directory="/app/static"), name="static")
templates = Jinja2Templates(directory="/app/templates")


def get_db_connection():
    conn = sqlite3.connect("/app/rss.db")
    conn.execute("pragma journal_mode=wal")
    conn.row_factory = sqlite3.Row
    return conn


def get_article(article_link_hash):
    conn = get_db_connection()
    article = conn.execute(
        'SELECT * FROM rss WHERE "article_link_hash" = ?', (article_link_hash,)
    ).fetchone()
    conn.close()
    if article is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return article


@app.exception_handler(StarletteHTTPException)
async def my_custom_exception_handler(Request: Request, exc: StarletteHTTPException):
    context = {"request": Request}
    return templates.TemplateResponse("ouch.html", context)


@app.get("/robots.txt")
def robots():
    data = """\
    User-agent: * 
    Disallow: \
    """
    return Response(content=data, media_type="text/plain")


@app.get("/", response_class=HTMLResponse)
async def index(Request: Request):
    now = time.time()
    conn = get_db_connection()
    news = conn.execute(
        f"SELECT * FROM rss WHERE article_date_published_epoch >= ({now} - 86400) ORDER BY article_date_published DESC"
    ).fetchall()
    stocks = conn.execute("SELECT * FROM stocks").fetchall()
    top = conn.execute(
        f"SELECT * FROM top WHERE article_date_published_epoch >= ({now} - 604800) ORDER BY score DESC LIMIT 6"
    ).fetchall()
    conn.close()
    context = {"request": Request, "news": news, "top": top, "stocks": stocks}
    return templates.TemplateResponse("index.html", context)


@app.get("/article/{article_link_hash}", response_class=HTMLResponse)
async def article(Request: Request, article_link_hash):
    article = get_article(article_link_hash)
    conn = get_db_connection()
    stocks = conn.execute("SELECT * FROM stocks").fetchall()
    context = {
        "request": Request,
        "article_date_published": article[0],
        "article_title": article[2],
        "article_link": article[3],
        "article_shortdesc": article[5],
        "article_image": article[6],
        "article_hnlink": article[7],
        "stocks": stocks,
    }
    return templates.TemplateResponse("article.html", context)


@app.get("/feed", response_class=HTMLResponse)
async def get_feed(Request: Request):
    def send_request():
        url = "https://cyberfeed.goatcounter.com/api/v0/count"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + GOAT_SECRET,
        }
        json = {"no_sessions": True, "hits": [{"path": "/feed"}]}
        return requests.post(url, headers=headers, json=json)

    response = send_request()
    context = {"request": Request}
    return templates.TemplateResponse("rss.xml", context, media_type="application/xml")
