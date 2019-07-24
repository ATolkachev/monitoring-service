FROM python:3.6-alpine3.8

ARG VERSION="dev"

LABEL Name="monitor-server" Version="$VERSION"\
      Description="Alexander's Monitoring Server Template" \
      Maintainer="Alexander Tolkachev <alexander.e.tolkachev@gmail.com>"

ARG TIME

RUN apk add git
RUN pip3.6 install -U setuptools
RUN pip3.6 install -e git+https://github.com/ATolkachev/monitoring-service#egg=monitoring
RUN apk del git

RUN adduser -D -u 1001 monitoring-server
USER monitoring-server

# Entrypoint directive is absent, due to using this image for different services
# It will be specified external
