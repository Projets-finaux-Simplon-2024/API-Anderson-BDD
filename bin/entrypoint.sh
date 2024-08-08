#!/bin/sh

# Appliquer les migrations Alembic
alembic upgrade head

# Démarrer l'application
uvicorn app.main:app --host 0.0.0.0 --port 8001
