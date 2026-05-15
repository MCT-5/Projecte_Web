#!/usr/bin/env bash

# Sortir immediatament si un comando falla
set -o errexit
# Entrar a la carpeta on està el manage.py
cd DjangoProject_prova
# Executar les migracions i el collectstatic usant poetry
poetry run python manage.py migrate
poetry run python manage.py collectstatic --no-input