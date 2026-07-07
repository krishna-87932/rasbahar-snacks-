#!/bin/bash
set -e
python -m pip install --disable-pip-version-check --no-cache-dir -r requirements.txt --break-system-packages
python manage.py migrate --noinput
python manage.py collectstatic --noinput
