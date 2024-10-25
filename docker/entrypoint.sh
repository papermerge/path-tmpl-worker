#!/bin/sh

exec_worker() {
  exec poetry run celery -A path_tmpl_worker.celery_app worker {PATH_TMPL_WORKER_ARGS}
}

case $1 in
  server)
    exec_worker
    ;;
  *)
    exec "$@"
    ;;
esac