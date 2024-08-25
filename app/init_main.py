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




# ------------------------------------------------------ Initialisation ------------------------------------------------------------------------|
def initialize_services():
    """Initialise toutes les dépendances externes, telles que MinIO, MLflow, etc."""
    load_dotenv()
    
    print("\nInitialisation Start... -----------------------------------------------------------------------------------------------------")

    def get_env_variable(var_name):
        """Helper function to get environment variable et print validation."""
        value = os.getenv(var_name)
        if value is None:
            print(f"\nErreur : La variable d'environnement {var_name} est manquante.")
            sys.exit(1)
        print(f"\nVariable d'environnement {var_name} : {value} chargée avec succès.")
        return value

    # Chargement et validation des variables d'environnement
    MINIO_URL = get_env_variable("MINIO_URL")
    MINIO_ACCESS_KEY = get_env_variable("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY = get_env_variable("MINIO_SECRET_KEY")
    MLFLOW_TRACKING_URI = get_env_variable("MLFLOW_TRACKING_URI")
    MLFLOW_DEFAULT_ARTIFACT_ROOT = get_env_variable("MLFLOW_DEFAULT_ARTIFACT_ROOT")
    AWS_ACCESS_KEY_ID = get_env_variable("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = get_env_variable("AWS_SECRET_ACCESS_KEY")
    MLFLOW_S3_ENDPOINT_URL = get_env_variable("MLFLOW_S3_ENDPOINT_URL")
    REACT_FRONT_URL = get_env_variable("REACT_APP_API_URL")

    # Initialiser le client Minio
    print("\nInitialisation du client Minio...")
    minio_client = Minio(
        MINIO_URL,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    print("Client Minio initialisé avec succès.")

    try:
        print("\nTest de la connexion à MinIO...")
        objects = minio_client.list_objects("mlflow")
        for obj in objects:
            print(f"Object: {obj.object_name}")
        print("Connexion à MinIO réussie.")
    except Exception as e:
        print(f"Erreur de connexion à MinIO: {str(e)}")
        print("Essayer d'installer le modèle via le script dans le dossier install_models")
        sys.exit(1)

    # Charger le modèle Solon depuis MLflow
    print("\nInitialisation de MLflow avec l'URI de suivi...")
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    print(f"MLflow URI de suivi défini sur {MLFLOW_TRACKING_URI}.")

    # Définissez l'URI de base pour les artefacts stockés dans MinIO
    print("\nInitialisation de l'experiment...")
    mlflow.set_experiment("Solon-embeddings")
    print(f"Experiment configuré sur {MLFLOW_TRACKING_URI}.")

    # Nom du modèle enregistré
    model_name_solon = "solon-embeddings-large-model"

    # Créer une instance de MlflowClient
    print("\nCréation du client MLflow...")
    client = MlflowClient()

    # Récupérer toutes les versions du modèle
    print(f"\nRécupération des versions du modèle {model_name_solon}...\n")
    model_versions = client.get_latest_versions(model_name_solon)

    # Filtrer la dernière version du modèle en fonction de l'ordre de version
    latest_version = max([int(version.version) for version in model_versions])
    print(f"\nLa dernière version du modèle {model_name_solon} est : {latest_version}.")

    # Charger le modèle depuis MLflow
    solon_model_uri = f"models:/solon-embeddings-large-model/{latest_version}"
    print(f"\nChargement du modèle depuis {solon_model_uri}...")
    solon_model = mlflow.pyfunc.load_model(solon_model_uri)
    if solon_model:
        print("Modèle chargé avec succès.")
    else:
        print("Erreur lors du chargement du modèle.")
        sys.exit(1)

    # Charger le tokenizer
    print("\nChargement du tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("OrdalieTech/Solon-embeddings-large-0.1")
    print("Tokenizer chargé avec succès.")

    return minio_client, client, solon_model, tokenizer, latest_version, REACT_FRONT_URL
# ----------------------------------------------------------------------------------------------------------------------------------------------|





# ------------------------------------------------------ Migration des tables si nécessaire ----------------------------------------------------|
# Vérifiez si les tables existent dans la base de données
def check_tables_exist(engine):
    inspector = inspect(engine)
    # Liste des tables nécessaires
    required_tables = ['documents', 'chunks', 'collections', 'users', 'roles']
    existing_tables = inspector.get_table_names()
    return all(table in existing_tables for table in required_tables)

def mig_tables():
    # Initialiser la base de données
    engine = database.engine

    # Vérifiez si les tables existent déjà
    if not check_tables_exist(engine):
        print("\nTables non trouvées, exécution de la migration...\n")
        call(["alembic", "upgrade", "head"])
    else:
        print("\nLes tables existent déjà, migration non nécessaire.\n")

    return engine
# ----------------------------------------------------------------------------------------------------------------------------------------------|