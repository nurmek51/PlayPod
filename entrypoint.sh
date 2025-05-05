#!/bin/bash
set -e

# Check for syntax errors in settings.py
echo "Checking for syntax errors in settings.py..."
python check_settings.py

# Try compiling the file to catch any syntax errors
python -m py_compile PlayPod/settings.py

python manage.py migrate --no-input
python manage.py collectstatic --no-input
exec "$@"
