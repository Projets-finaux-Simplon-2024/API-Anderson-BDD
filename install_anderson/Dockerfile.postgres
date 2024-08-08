# Dockerfile

# Utiliser l'image PostgreSQL officielle comme base
FROM postgres:latest

# Installer les dépendances nécessaires
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-server-dev-all \
    git \
    && rm -rf /var/lib/apt/lists/*

# Cloner le dépôt pgvector et installer l'extension
RUN git clone --branch v0.4.1 https://github.com/pgvector/pgvector.git /usr/src/pgvector \
    && cd /usr/src/pgvector \
    && make \
    && make install

# Supprimer les fichiers sources pour réduire la taille de l'image
RUN rm -rf /usr/src/pgvector

# Définir la commande par défaut pour démarrer PostgreSQL
CMD ["postgres"]
