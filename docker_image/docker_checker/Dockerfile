FROM monitor-template

ARG VERSION="dev"

LABEL Name="checker-server" Version="$VERSION"\
      Description="Alexander's Monitoring Server Checker" \
      Maintainer="Alexander Tolkachev <alexander.e.tolkachev@gmail.com>"

USER monitoring-server

ENTRYPOINT monitor-checker