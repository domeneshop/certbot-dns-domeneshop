FROM certbot/certbot:v2.10.0

COPY . /opt/certbot/src/plugin

RUN python tools/pip_install.py --no-cache-dir --editable /opt/certbot/src/plugin