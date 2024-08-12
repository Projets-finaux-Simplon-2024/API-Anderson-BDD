# Utilisez une image Python 3.12-slim de base
FROM python:3.12-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier le fichier des dépendances et installer les dépendances
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# Copier le reste de l'application
COPY . .

# Exposer le port que l'application va utiliser
EXPOSE 8080

# Commande pour démarrer l'application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
