#!/bin/sh

cd ..

set -e

alembic upgrade head

exec "$@"