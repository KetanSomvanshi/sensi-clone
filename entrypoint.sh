#!/bin/sh

python --version
echo "Current working directory: `pwd`"
echo "App run command args: $@"

# we will h=have different commands to run server , worker and scheduler
run_service() {
  echo "Generated config, starting sensi app..."
  env $(cat /code/config/.env | xargs) /usr/local/bin/uvicorn server.app:app --host=0.0.0.0 --port=19093 --workers=4
}

run_worker() {
  echo "Generated config, starting sensi workers..."
  env $(cat /code/config/.env | xargs)  /usr/local/bin/celery -A worker.scheduler beat
}

run_scheduler() {
  echo "Generated config, starting sensi scheduler..."
  env $(cat /code/config/.env | xargs)  /usr/local/bin/celery -A worker.task_worker worker
}

CMD_TO_EXECUTE="$1"

# depending on the command we will run the respective function
case "$CMD_TO_EXECUTE" in
  "run_app")
    run_service
    exit $?
  ;;
  "run_worker")
    run_worker
    exit $?
  ;;
  "run_scheduler")
    run_scheduler
    exit $?
esac

exec "$@"