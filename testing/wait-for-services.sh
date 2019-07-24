#!/bin/bash

set -e

MONGO_HOST=${MONGO_HOST:-mongodb}
MONGO_PORT=${MONGO_PORT:-27017}

RABBITMQ_HOST=${RABBITMQ_HOST:-rabbitmq}
RABBITMQ_PORT=${RABBITMQ_PORT:-5672}

cmd="$@"

exec 1>&2

function check_service() {
	host=$1
	port=$2

	until nc -z "$host" "$port"; do
  		echo "$host:$port is unavailable - sleeping"
  		sleep 5
	done
}

check_service ${RABBITMQ_HOST} ${RABBITMQ_PORT}
check_service ${MONGO_HOST} ${MONGO_PORT}

echo "Services are up and running - executing command \"$cmd\""
exec $cmd
