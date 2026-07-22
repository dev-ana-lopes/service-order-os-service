#!/usr/bin/env sh
set -eu

should_migrate="${MIGRATE_ON_STARTUP:-true}"

python - <<'PY'
import os
import socket
import sys
from urllib.parse import urlparse

database_url = os.environ.get("DATABASE_URL", "").strip()

if not database_url:
    print("[entrypoint] DATABASE_URL is required", flush=True)
    sys.exit(1)

parsed = urlparse(database_url)
host = parsed.hostname
port = parsed.port
database = parsed.path.lstrip("/")

if not host or not port or not database:
    print(
        "[entrypoint] DATABASE_URL must include host, port, and database name",
        flush=True,
    )
    sys.exit(1)

print(
    f"[entrypoint] Database target host={host} port={port} db={database}",
    flush=True,
)

try:
    resolved = sorted(
        {
            result[4][0]
            for result in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        }
    )
except OSError as exc:
    print(
        f"[entrypoint] Database host resolution failed for host={host}: {exc}",
        flush=True,
    )
else:
    print(
        f"[entrypoint] Database host resolved to: {', '.join(resolved)}",
        flush=True,
    )
PY

if [ "$should_migrate" != "false" ]; then
  echo "[entrypoint] MIGRATE_ON_STARTUP requested, but local Docker bootstrap uses SQLAlchemy create_all and skips Alembic."
fi

echo "[entrypoint] Starting application: $*"
exec "$@"
