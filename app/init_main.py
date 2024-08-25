# ------------------------------------------------------ Imports -------------------------------------------------------------------------------|
# Standard library imports
import os
import sys
from subprocess import call

# Third-party library imports
from sqlalchemy import inspect
from minio import Minio
from minio.commonconfig import REPLACE
from dotenv import load_dotenv
from transformers import AutoTokenizer
from mlflow.tracking import MlflowClient
import mlflow.pyfunc
import mlflow

# Local application imports
from . import database
# ----------------------------------------------------------------------------------------------------------------------------------------------|


# ------------------------------------------------------ Récupére var d'env --------------------------------------------------------------------|
def get_env_variable(var_name):
    """Helper function to get environment variable et print validation."""
    value = os.getenv(var_name)
    if value is None:
        print(f"\033[91mErreur : La variable d'environnement {var_name} est manquante.\033[0m")
        sys.exit(1)
    print(f"\033[92mVariable d'environnement {var_name} : {value} chargée avec succès.\033[0m")
    return value
# ----------------------------------------------------------------------------------------------------------------------------------------------|


# ------------------------------------------------------ Initialisation ------------------------------------------------------------------------|
def initialize_services():
    """Initialise toutes les dépendances externes, telles que MinIO, MLflow, etc."""
    load_dotenv()
    print("\033[94mChargement et validation des variables d'environnement...\033[0m")

    # Chargement et validation des variables d'environnement
    MINIO_URL = get_env_variable("MINIO_URL")
    MINIO_ACCESS_KEY = get_env_variable("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY = get_env_variable("MINIO_SECRET_KEY")
    MLFLOW_TRACKING_URI = get_env_variable("MLFLOW_TRACKING_URI")
    MLFLOW_DEFAULT_ARTIFACT_ROOT = get_env_variable("MLFLOW_DEFAULT_ARTIFACT_ROOT")
    AWS_ACCESS_KEY_ID = get_env_variable("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = get_env_variable("AWS_SECRET_ACCESS_KEY")
    MLFLOW_S3_ENDPOINT_URL = get_env_variable("MLFLOW_S3_ENDPOINT_URL")

    # Initialiser le client Minio
    print("\n\033[94mInitialisation du client Minio...\033[0m")
    minio_client = Minio(
        MINIO_URL,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    print("\033[92mClient Minio initialisé avec succès.\033[0m")

    try:
        print("\033[94mTest de la connexion à MinIO...\033[0m")
        objects = minio_client.list_objects("mlflow")
        for obj in objects:
            print(f"\033[96mObjet trouvé : {obj.object_name}\033[0m")
        print("\033[92mConnexion à MinIO réussie.\033[0m")
    except Exception as e:
        print(f"\033[91mErreur de connexion à MinIO : {str(e)}\033[0m")
        print("\033[93mEssayer d'installer le modèle via le script dans le dossier install_models\033[0m")
        sys.exit(1)

    # Charger le modèle Solon depuis MLflow
    print("\n\033[94mInitialisation de MLflow avec l'URI de suivi...\033[0m")
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    print(f"\033[92mMLflow URI de suivi défini sur {MLFLOW_TRACKING_URI}.\033[0m")

    # Initialisation de l'expérience MLflow
    print("\033[94mInitialisation de l'expérience MLflow...\033[0m")
    mlflow.set_experiment("Solon-embeddings")
    print(f"\033[92mExpérience configurée sur {MLFLOW_TRACKING_URI}.\033[0m")

    # Nom du modèle enregistré
    model_name_solon = "solon-embeddings-large-model"

    # Créer une instance de MlflowClient
    print("\033[94mCréation du client MLflow...\033[0m")
    client = MlflowClient()

    # Récupérer toutes les versions du modèle
    print(f"\n\033[94mRécupération des versions du modèle {model_name_solon}...\033[0m")
    model_versions = client.get_latest_versions(model_name_solon)

    # Filtrer la dernière version du modèle en fonction de l'ordre de version
    latest_version = max([int(version.version) for version in model_versions])
    print(f"\033[92mLa dernière version du modèle {model_name_solon} est : {latest_version}.\033[0m")

    # Charger le modèle depuis MLflow
    solon_model_uri = f"models:/solon-embeddings-large-model/{latest_version}"
    print(f"\n\033[94mChargement du modèle depuis {solon_model_uri}...\033[0m")
    solon_model = mlflow.pyfunc.load_model(solon_model_uri)
    if solon_model:
        print("\033[92mModèle chargé avec succès.\033[0m")
    else:
        print("\033[91mErreur lors du chargement du modèle.\033[0m")
        sys.exit(1)

    # Charger le tokenizer
    print("\n\033[94mChargement du tokenizer...\033[0m")
    tokenizer = AutoTokenizer.from_pretrained("OrdalieTech/Solon-embeddings-large-0.1")
    print("\033[92mTokenizer chargé avec succès.\033[0m")

    return minio_client, client, solon_model, tokenizer, latest_version
# ----------------------------------------------------------------------------------------------------------------------------------------------|


# ------------------------------------------------------ Migration des tables si nécessaire ----------------------------------------------------|
def check_tables_exist(engine):
    inspector = inspect(engine)
    required_tables = ['documents', 'chunks', 'collections', 'users', 'roles']
    existing_tables = inspector.get_table_names()
    return all(table in existing_tables for table in required_tables)

def mig_tables():
    engine = database.engine
    if not check_tables_exist(engine):
        print("\n\033[94mTables non trouvées, exécution de la migration...\033[0m")
        call(["alembic", "upgrade", "head"])
    else:
        print("\n\033[92mLes tables existent déjà, migration non nécessaire.\033[0m")
    return engine
# ----------------------------------------------------------------------------------------------------------------------------------------------|
