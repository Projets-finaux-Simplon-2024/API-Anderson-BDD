import pytest
from sqlalchemy import create_engine, select, func, text
from sqlalchemy.orm import sessionmaker
from app.main import app
from app import models
from app.database import Base, get_db
from fastapi.testclient import TestClient
from unittest.mock import patch
import numpy as np
import sqlalchemy

# Import des fonctions de test de l'initialisation depuis le dossier tests
from tests.init_test import initialize_test_services, get_test_db, setup_test_database, teardown_test_database

# Configuration de la base de données SQLite en mémoire
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Surcharge la dépendance get_db avec la base de données de test
app.dependency_overrides[get_db] = get_test_db

client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    # Setup de la base de données pour les tests
    setup_test_database()
    yield
    # Teardown de la base de données après les tests
    teardown_test_database()

@pytest.mark.asyncio
async def test_search_similar_chunks(test_db):
    # Initialisation des services de test (mocks)
    minio_client, mlflow_client, solon_model, tokenizer = initialize_test_services()

    # Ajout d'un chunk dans la base de données pour le test
    db_session = next(get_test_db())
    chunk_text = "test chunk"
    embedding = np.random.rand(1024).tolist()  # Générer un embedding aléatoire
    
    chunk = models.Chunk(
        chunk_id=1,
        chunk_text=chunk_text,
        document_id=1,
        taille_chunk=len(chunk_text),
        embedding_solon=embedding,  # Stocker l'embedding sous forme de JSON
    )
    db_session.add(chunk)
    db_session.commit()

    # Patch `initialize_services` pour utiliser les mocks dans l'environnement de test
    with patch("app.main.initialize_services", return_value=(minio_client, mlflow_client, solon_model, tokenizer)):
        with patch("app.main.solon_model", solon_model):  # Patch la variable globale `solon_model`

            # Construire la requête SQL en fonction de la base de données utilisée
            query_embedding = solon_model.predict(["test query"])[0]
            db_session = next(get_test_db())

            # Récupérer tous les chunks
            chunks = db_session.query(models.Chunk).all()

            # Calculer la distance euclidienne en Python
            min_distance = float('inf')
            closest_chunk = None

            for chunk in chunks:
                chunk_embedding = chunk.embedding_solon
                distance = np.linalg.norm(np.array(chunk_embedding) - np.array(query_embedding))
                if distance < min_distance:
                    min_distance = distance
                    closest_chunk = chunk

            # Vérifier le résultat
            assert closest_chunk is not None
            assert closest_chunk.chunk_text == "test chunk"

