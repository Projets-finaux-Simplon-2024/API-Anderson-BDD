# Utiliser une image de base Python
FROM python:3.12

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de l'application
COPY . .

# Installer les dépendances
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copier le script d'entrypoint
COPY entrypoint.sh /entrypoint.sh

# Exposer le port 8001
EXPOSE 8001

# Définir le script d'entrypoint
ENTRYPOINT ["/bin/entrypoint.sh"]
