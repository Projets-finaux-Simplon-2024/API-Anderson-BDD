import os
import sys
from unittest.mock import MagicMock
import mlflow.pyfunc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base

# Initialiser une base de données SQLite en mémoire pour les tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def initialize_test_services():
    """
    Initialise les services avec des mocks pour les tests.
    """
    print("\nInitialisation des services de test...")

    # Mock MinIO client
    mock_minio_client = MagicMock()
    print("Mock MinIO client initialisé.")

    # Mock MLflow client
    mock_mlflow_client = MagicMock()
    print("Mock MLflow client initialisé.")

    # Mock modèle Solon
    mock_solon_model = MagicMock()
    mock_solon_model.predict.return_value = [list(range(1024))]  # Retourne un vecteur constant pour les tests
    print("Mock modèle Solon initialisé.")

    # Mock tokenizer
    mock_tokenizer = MagicMock()
    print("Mock tokenizer initialisé.")
    print("Fin d'initialisation des services de test...")

    return mock_minio_client, mock_mlflow_client, mock_solon_model, mock_tokenizer

def setup_test_database():
    """
    Configure la base de données en mémoire pour les tests.
    """
    Base.metadata.create_all(bind=engine)

def teardown_test_database():
    """
    Nettoie la base de données après les tests.
    """
    Base.metadata.drop_all(bind=engine)

def get_test_db():
    """
    Dépendance de base de données pour les tests.
    """
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()
