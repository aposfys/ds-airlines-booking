#!/bin/sh
# Apply migrations before serving. Schema creation is Alembic's job, not the
# application's — the app no longer calls create_all at startup, so a
# container that skipped this would serve against an empty database.
set -e

echo "Applying database migrations…"
alembic upgrade head

echo "Starting API…"
exec "$@"
