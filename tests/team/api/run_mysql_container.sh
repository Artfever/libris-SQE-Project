#!/usr/bin/env bash
set -euo pipefail

output=${1:?Usage: run_mysql_container.sh EVIDENCE.json}
container=libris-sqe-mysql-$(python -c 'import secrets; print(secrets.token_hex(8))')
export MYSQL_ROOT_PASSWORD=$(python -c 'import secrets; print(secrets.token_urlsafe(30))')
export MYSQL_PASSWORD=$(python -c 'import secrets; print(secrets.token_urlsafe(30))')
export MYSQL_DATABASE=libris_sqe MYSQL_USER=libris_sqe
export LIBRIS_SQE_MYSQL_PASSWORD=$MYSQL_PASSWORD

docker run --rm --detach --name "$container" --publish 127.0.0.1:13384:3306 \
  --env MYSQL_ROOT_PASSWORD --env MYSQL_PASSWORD --env MYSQL_DATABASE --env MYSQL_USER mysql:8.4 >/dev/null
cleanup() {
  docker stop "$container" >/dev/null
}
trap cleanup EXIT

mysql_root() {
  docker exec -i "$container" sh -ec 'export MYSQL_PWD="$MYSQL_ROOT_PASSWORD"; exec mysql -h 127.0.0.1 -uroot "$@"' _ "$@"
}

for ((attempt=1; attempt<=90; attempt++)); do
  if mysql_root -e 'SELECT 1' >/dev/null 2>&1; then
    mysql_root <<'SQL'
GRANT SELECT ON performance_schema.data_lock_waits TO 'libris_sqe'@'%';
GRANT SELECT ON performance_schema.data_locks TO 'libris_sqe'@'%';
SQL
    python tests/team/api/run_mysql_concurrency.py --output "$output"
    exit
  fi
  sleep 1
done
printf '%s\n' 'Disposable MySQL failed to become ready' >&2
exit 1
