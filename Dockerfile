ARG VERSION=v2.7.4
FROM certbot/certbot:2.8.0

ENV PYTHONIOENCODING="UTF-8"

COPY . src/certbot-dns-domeneshop

RUN pip install -U pip
RUN pip install --no-cache-dir src/certbot-dns-domeneshop

ENTRYPOINT ["/usr/bin/env"]