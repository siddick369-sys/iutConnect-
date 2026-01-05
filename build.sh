#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Collecte les fichiers statiques
python manage.py collectstatic --no-input
