<div align="center">

<img src="icons8-néo-480.png" alt="Logo Anderson" width="140">

# Anderson — API de recherche sémantique pour RAG

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![MLflow](https://img.shields.io/badge/MLflow-Model_registry-0194E2?logo=mlflow&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-Object_storage-C72E49?logo=minio&logoColor=white)

**Gestion documentaire, embeddings et recherche vectorielle pour alimenter un pipeline RAG.**

</div>

Anderson est une API FastAPI permettant d’organiser des documents en collections, de les stocker dans MinIO, de les découper en chunks, de calculer leurs embeddings et d’effectuer une recherche sémantique avec PostgreSQL et pgvector.

Le projet complet intègre également une authentification JWT, une gestion des utilisateurs et de leurs permissions, le versionnement des modèles avec MLflow ainsi qu’une suite de tests automatisés.

→ **Code source complet :** [GitHub — API Anderson](https://github.com/Projets-finaux-Simplon-2024/API-Anderson-BDD)<br>
&nbsp;&nbsp;&nbsp;&nbsp;↳ **Démo publique simplifiée :** [Hugging Face Spaces](https://huggingface.co/spaces/JeremyMikaleff/Anderson-Semantic_Retrieval_for_RAG)

> La démo Hugging Face Spaces est une version allégée du projet. Elle utilise une base PostgreSQL distante et un modèle d’embedding directement chargé depuis Hugging Face, sans la chaîne locale MinIO/MLflow.

## 📑 Table des matières

- [Fonctionnalités](#fonctionnalites)
- [Architecture locale](#architecture-locale)
- [Prérequis](#prerequis)
- [Installation automatique sous Windows](#installation-windows)
- [Installation des modèles dans MLflow](#installation-modeles)
- [Commandes Docker Compose](#commandes-docker-compose)
- [Lancement local avec Python](#lancement-python)
- [Construction manuelle de l’image](#construction-image)
- [Ancienne commande Docker de test](#ancienne-commande-docker)
- [Versionnement de la base avec Alembic](#alembic)
- [Tests automatisés](#tests)
- [Sécurité et configuration](#securite)
- [Démonstration en ligne](#demonstration)
- [Différences entre les deux versions](#difference)

<a id="fonctionnalites"></a>
## ✨ Fonctionnalités

- API REST développée avec FastAPI et documentation Swagger interactive ;
- authentification JWT et gestion des utilisateurs, rôles et permissions ;
- création et gestion de collections documentaires ;
- import, extraction, découpage et stockage des documents avec MinIO ;
- génération et stockage d’embeddings dans PostgreSQL avec pgvector ;
- recherche sémantique par similarité cosinus ;
- récupération des chunks pertinents afin d’alimenter un pipeline RAG ;
- registre, versionnement et suivi des modèles avec MLflow ;
- métriques applicatives exposées pour Prometheus ;
- tests automatisés avec pytest.

<a id="architecture-locale"></a>
## 🏗️ Architecture locale

L’installation Docker locale démarre les services suivants :

| Service | Rôle | Adresse locale |
|---|---|---|
| FastAPI | API et documentation Swagger | `http://localhost:8080` |
| PostgreSQL + pgvector | Métadonnées, chunks et vecteurs | `localhost:5432` |
| MinIO | Documents et artefacts MLflow | `http://localhost:9000` |
| Console MinIO | Administration du stockage | `http://localhost:9001` |
| MLflow | Registre et suivi des modèles | `http://localhost:5000` |

<a id="prerequis"></a>
## ✅ Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) démarré ;
- Docker Compose ;
- [Python 3.12](https://www.python.org/downloads/) pour une exécution hors Docker ;
- Git ;
- Jupyter Notebook pour exécuter le notebook d’installation du modèle Solon dans MLflow.

Sous Windows, Docker Desktop doit être opérationnel avant de lancer les scripts `.bat`.

<a id="installation-windows"></a>
## 🚀 Installation automatique sous Windows

Le dossier `install_anderson` contient les fichiers nécessaires au lancement de l’infrastructure :

- `win_install.bat` crée le réseau Docker de monitoring s’il n’existe pas, puis construit et démarre les conteneurs ;
- `win_uninstall.bat` arrête l’installation et supprime ses conteneurs, images et volumes ;
- `docker-compose.yml` décrit PostgreSQL/pgvector, MinIO, MLflow et FastAPI ;
- `Dockerfile.postgres` construit l’image PostgreSQL avec pgvector ;
- `init.sql` active l’extension `vector`.

Depuis l’explorateur Windows, exécuter :

```text
install_anderson\win_install.bat
```

Ou depuis PowerShell :

```powershell
cd .\install_anderson
.\win_install.bat
```

Le script ouvre une console et lance automatiquement les conteneurs.

Une fois l’infrastructure démarrée, installer le modèle Solon dans MLflow à l’aide du notebook présent dans le dossier `install_models`.

> ⚠️ `win_uninstall.bat` utilise `docker-compose down --rmi all -v`. Il supprime donc également les images et les volumes Docker de cette installation, y compris les données locales PostgreSQL, MinIO et MLflow.

<a id="installation-modeles"></a>
## 🧠 Installation des modèles dans MLflow

Le dossier `install_models` référence les trois modèles étudiés pendant le projet :

- `Solon-embeddings-large-0.1.ipynb` — notebook fonctionnel pour `OrdalieTech/Solon-embeddings-large-0.1` ;
- `BGE-m3-custom-fr.ipynb` — emplacement prévu pour un modèle BGE-M3 adapté au français ;
- `Cohere-embed-multilingual-v3.0.ipynb` — emplacement prévu pour Cohere Embed Multilingual v3.0.

Dans l’état actuel du dépôt, seul le notebook Solon contient le pipeline complet d’enregistrement du modèle dans MLflow. Les fichiers BGE et Cohere sont présents mais vides.

### Ordre d’installation recommandé

1. Démarrer l’infrastructure avec `install_anderson\win_install.bat`.
2. Vérifier que MLflow est accessible sur `http://localhost:5000`.
3. Ouvrir `install_models/Solon-embeddings-large-0.1.ipynb`.
4. Exécuter les cellules du notebook.
5. Vérifier le modèle et sa version depuis l’interface MLflow.

Les trois modèles ont été envisagés pendant le projet. Solon est celui qui a bénéficié de l’intégration et du suivi complets dans l’API, compte tenu du temps et des ressources disponibles.

<a id="commandes-docker-compose"></a>
## 🐳 Commandes Docker Compose

Les commandes historiques du projet utilisent le nom `bdd_anderson`.

### Construire et démarrer les services

```powershell
docker-compose -p bdd_anderson up --build -d
```

### Démarrer les services sans reconstruire les images

```powershell
docker-compose -p bdd_anderson up -d
```

### Arrêter et supprimer les conteneurs et réseaux Compose

```powershell
docker-compose -p bdd_anderson down
```

Cette commande :

- arrête les conteneurs ;
- supprime les conteneurs ;
- supprime les réseaux créés par Docker Compose ;
- conserve les volumes par défaut ;
- conserve les images par défaut.

Pour supprimer également les volumes et les images :

```powershell
docker-compose -p bdd_anderson down -v --rmi all
```

> ⚠️ Cette variante est destructive : elle supprime les volumes et donc les données locales persistantes.

### Redémarrer des conteneurs déjà créés

```powershell
docker-compose -p bdd_anderson start
```

### Arrêter les conteneurs sans les supprimer

```powershell
docker-compose -p bdd_anderson stop
```

Avec une version récente de Docker Desktop, la syntaxe `docker compose` peut remplacer `docker-compose` :

```powershell
docker compose -p bdd_anderson up --build -d
```

<a id="lancement-python"></a>
## 🐍 Lancement local de l’API avec Python

Le script `lancement_api.bat` automatise :

1. la création de l’environnement virtuel `env_api_anderson` ;
2. son activation ;
3. la mise à jour de pip ;
4. l’installation des dépendances ;
5. le démarrage d’Uvicorn.

Pour le lancer :

```powershell
.\lancement_api.bat
```

### Équivalent manuel

```powershell
py -3.12 -m venv env_api_anderson
.\env_api_anderson\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

L’infrastructure PostgreSQL, MinIO et MLflow doit être accessible et les variables d’environnement attendues par l’application doivent être définies.

<a id="construction-image"></a>
## 📦 Construction manuelle de l’image de l’API

Depuis la racine du dépôt :

```powershell
docker build --no-cache -t api-anderson .
```

Pour éviter d’inscrire les mots de passe, les clés JWT ou les adresses internes dans l’historique du terminal, placer la configuration dans un fichier `.env.docker` ignoré par Git :

```dotenv
SUPER_USER=superuser
SUPER_PASSWORD=<mot-de-passe-hache-bcrypt>
SECRET_KEY=<cle-secrete-aleatoire>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

MINIO_URL=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

MLFLOW_TRACKING_URI=http://mlflow:5000
MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://mlflow/artifacts
MLFLOW_S3_ENDPOINT_URL=http://minio:9000

AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin

DATABASE_URL=postgresql://admin:admin@db:5432/anderson
REACT_FRONT_URL=http://localhost:3000
```

Puis lancer le conteneur sur le réseau créé par l’installation Docker :

```powershell
docker run -d `
  --name fastapi_container `
  --env-file .env.docker `
  -p 8080:8080 `
  --network container_anderson_back_office_network `
  api-anderson
```

Le nom exact du réseau peut être vérifié avec :

```powershell
docker network ls
```

<a id="ancienne-commande-docker"></a>
### 🕰️ Ancienne commande Docker utilisée pour les tests locaux

La commande suivante était utilisée pendant le développement pour injecter directement toutes les variables d’environnement dans le conteneur :

```powershell
docker run -d --name fastapi_container -e SUPER_USER=superuser -e SUPER_PASSWORD='$2b$12$j9jsBsgf87konm6b5qxnr.OK2xZOLIVPDULPCfkjfML7ZYn7FjT2O' -e SECRET_KEY=75bdaa1397df51c94112f76b70cd62221b3bd97fd9ae35d07edc5fcd02dff068 -e ALGORITHM=HS256 -e ACCESS_TOKEN_EXPIRE_MINUTES=30 -e MINIO_URL=172.18.0.3:9000 -e MINIO_ACCESS_KEY=minioadmin -e MINIO_SECRET_KEY=minioadmin -e MLFLOW_TRACKING_URI=http://172.18.0.4:5000 -e MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://mlflow/artifacts -e AWS_ACCESS_KEY_ID=minioadmin -e AWS_SECRET_ACCESS_KEY=minioadmin -e MLFLOW_S3_ENDPOINT_URL=http://172.18.0.3:9000 -e DATABASE_URL=postgresql://admin:admin@172.18.0.2/anderson -p 8080:8080 --network container_anderson_back_office_default mon-image
```

<a id="alembic"></a>
## 🗃️ Versionnement de la base de données avec Alembic

Alembic est déjà initialisé dans ce dépôt. Il ne faut donc pas relancer `alembic init` pour une utilisation normale.

### Créer une migration

Après une modification des modèles SQLAlchemy :

```powershell
alembic revision --autogenerate -m "Updated models"
```

Le fichier généré doit être vérifié avant d’être appliqué.

### Appliquer les migrations

```powershell
alembic upgrade head
```

### Afficher la révision courante

```powershell
alembic current
```

### Vérifier la cohérence entre les modèles et la base

```powershell
alembic check
```

La commande utilisée lors de la création initiale de la configuration Alembic était :

```powershell
alembic init versioning_bdd
```

<a id="tests"></a>
## 🧪 Tests automatisés

Depuis la racine du projet et avec les dépendances installées :

```powershell
pytest
```

La suite de tests couvre notamment :

- la connexion à la base de données ;
- l’authentification ;
- la génération et la validation des jetons JWT ;
- la gestion des utilisateurs ;
- la gestion des collections ;
- l’import et la suppression des documents ;
- la recherche de chunks similaires.

<a id="securite"></a>
## 🔐 Sécurité et configuration

Les identifiants présents dans `install_anderson/docker-compose.yml` sont des valeurs de démonstration destinées exclusivement à une exécution locale.

Ils doivent être remplacés avant toute exposition du projet sur un réseau partagé ou en production.

Ne jamais versionner :

- un fichier `.env` contenant des secrets ;
- une clé JWT réelle ;
- un mot de passe PostgreSQL ou MinIO utilisé en production ;
- un jeton d’accès Hugging Face, GitHub, Cohere ou d’un autre fournisseur ;
- des identifiants directement dans une commande `docker run`.

<a id="demonstration"></a>
## 🌐 Démonstration en ligne

Une version simplifiée et publique de l’API est déployée sur Hugging Face Spaces :

- [ouvrir la démonstration Anderson](https://huggingface.co/spaces/JeremyMikaleff/Anderson-Semantic_Retrieval_for_RAG) ;
- [consulter les fichiers du Space](https://huggingface.co/spaces/JeremyMikaleff/Anderson-Semantic_Retrieval_for_RAG/tree/main).

Cette version permet :

- de créer et gérer des collections ;
- d’importer et supprimer des documents ;
- d’extraire et découper leur contenu ;
- de calculer les embeddings ;
- d’effectuer une recherche vectorielle ;
- d’envoyer une question ;
- de récupérer un prompt enrichi prêt à être transmis à un LLM.

<a id="difference"></a>
## 📌 Différences entre les deux versions

| Projet GitHub complet | Démo Hugging Face Spaces |
|---|---|
| Authentification JWT | Accès public sans compte |
| Gestion des utilisateurs et rôles | Gestion des utilisateurs retirée |
| Documents stockés dans MinIO | Documents originaux supprimés après traitement |
| Modèles suivis avec MLflow | Modèle chargé depuis Hugging Face |
| Infrastructure Docker Compose complète | Un seul conteneur Docker |
| PostgreSQL/pgvector local | PostgreSQL/pgvector hébergé sur Neon |
| Monitoring et tests complets | Démonstration fonctionnelle simplifiée |
| Recherche des chunks similaires | Génération directe d’un prompt enrichi |

