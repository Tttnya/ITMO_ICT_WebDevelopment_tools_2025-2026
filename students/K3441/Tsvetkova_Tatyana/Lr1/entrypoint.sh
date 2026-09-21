#!/bin/sh
set -e

if [ "$SKIP_MIGRATIONS" != "1" ]; then
  alembic upgrade head
fi

exec "$@"
