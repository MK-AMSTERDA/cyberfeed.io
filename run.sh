#!/bin/bash

# Bring down SQLite Database
litestream restore -o /app/rss.db s3://ls-cyberfeed

litestream replicate -exec "uvicorn app.main:app --host 0.0.0.0 --port 8000" & supercronic /app/crontab