FROM python:slim as builder

RUN apt-get update && apt-get install -y wget curl --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN LITESTREAM_RELEASE=$(curl -I https://github.com/benbjohnson/litestream/releases/latest | awk -F '/' '/^location/ {print  substr($NF, 1, length($NF)-1)}' | sed 's/%0D//g') \
    && wget https://github.com/benbjohnson/litestream/releases/download/$LITESTREAM_RELEASE/litestream-$LITESTREAM_RELEASE-linux-amd64-static.tar.gz -O /tmp/litestream.tar.gz

RUN tar -C /usr/local/bin -xzf /tmp/litestream.tar.gz

RUN SUPERCRONIC_RELEASE=$(curl -I https://github.com/aptible/supercronic/releases/latest | awk -F '/' '/^location/ {print  substr($NF, 1, length($NF)-1)}' | sed 's/%0D//g') \
    && wget https://github.com/aptible/supercronic/releases/download/$SUPERCRONIC_RELEASE/supercronic-linux-amd64 -O /usr/local/bin/supercronic && chmod +x "/usr/local/bin/supercronic"

COPY . /app

FROM python:slim

COPY --from=builder /app /app
COPY --from=builder /usr/local/bin/litestream /usr/local/bin/litestream
COPY --from=builder /usr/local/bin/supercronic /usr/local/bin/supercronic
COPY ./litestream.yml /etc/litestream.yml

RUN addgroup --system app && adduser --system --group app

RUN apt-get update && apt-get install -y htop --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/home/app/.local/bin:${PATH}"
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade --no-cache-dir -r /app/requirements/app.txt


RUN chmod +x /app/run.sh && mkdir /app/log && chown -R app:app /app

EXPOSE 8000

USER app

CMD [ "/app/run.sh" ]
