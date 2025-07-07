#!/bin/bash

redis-server --daemonize yes --port 24779 --dir /usr/src/app/redis-dir

celery -A celery_task worker --loglevel=warning -Ofair  > celery.logs 2>&1 &

exec python3 server.py