#!/bin/sh

echo "in entrypoint"

echo "argument $1"

exec_worker() {
  echo "now in exec_worker"
  exec poetry run celery -A path_tmpl_worker.celery_app worker ${PATH_TMPL_WORKER_ARGS}
}

case $1 in
  worker)
    exec_worker
    ;;
  *)
    exec "$@"
    ;;
esac
