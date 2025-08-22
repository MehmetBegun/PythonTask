#!/bin/bash
set -e

sleep 5

PG_VER=${PG_VER:-15}
PG_DATA=/var/lib/postgresql/${PG_VER}/main
PG_BIN=/usr/lib/postgresql/${PG_VER}/bin

mkdir -p /var/lib/postgresql/${PG_VER} /var/log/postgresql
chown -R postgres:postgres /var/lib/postgresql /var/log/postgresql

if [ ! -d "$PG_DATA" ] || [ -z "$(ls -A "$PG_DATA" 2>/dev/null)" ]; then
  echo "Initializing PostgreSQL cluster at $PG_DATA"
  su postgres -c "${PG_BIN}/initdb -D '$PG_DATA'"
fi

echo "Starting PostgreSQL..."
su postgres -c "${PG_BIN}/pg_ctl -D '$PG_DATA' -l /var/log/postgresql/postgres.log start"

for i in {1..30}; do
  if su postgres -c "${PG_BIN}/pg_isready -q"; then
    break
  fi
  sleep 1
done

DB_NAME_ENV=${DB_NAME:-postgres_db}
DB_PASSWORD_ENV=${DB_PASSWORD:-postgres}
su postgres -c "psql -U postgres -tc \"SELECT 1 FROM pg_database WHERE datname='${DB_NAME_ENV}'\" | grep -q 1 || createdb -U postgres '${DB_NAME_ENV}'" || true
su postgres -c "psql -U postgres -c \"alter user postgres password '${DB_PASSWORD_ENV}';\"" || true

python /app/consumer_db.py &
python /app/webapp.py