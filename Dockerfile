FROM docker.io/alpine:3.10

ENV UID=1337 \
    GID=1337

RUN apk add --no-cache  \
      py3-pillow \
      py3-aiohttp \
      py3-magic \
      py3-sqlalchemy \
      py3-psycopg2 \
      py3-ruamel.yaml \
      # Indirect dependencies
      #commonmark
        py3-future \
      #alembic
        py3-mako \
        py3-dateutil \
        py3-markupsafe \
        py3-six \
      py3-idna \
      # Other dependencies
      ca-certificates \
      su-exec

COPY . /opt/mautrix-twilio
WORKDIR /opt/mautrix-twilio
RUN pip3 install .

VOLUME /data

CMD ["/opt/mautrix-twilio/docker-run.sh"]
