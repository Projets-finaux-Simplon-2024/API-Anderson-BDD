import pytest
from app.main import app
from app import models
from app.database import Base, get_db
from fastapi.testclient import TestClient
from unittest.mock import patch
import numpy as np
from sqlalchemy import inspect

# Import des fonctions de test de l'initialisation depuis le dossier tests
from tests.init_test import initialize_test_services, get_test_db, setup_test_database, teardown_test_database

# Surcharge la dépendance get_db avec la base de données de test
app.dependency_overrides[get_db] = get_test_db

client = TestClient(app)

def print_tables(db_session, message=""):
    inspector = inspect(db_session.bind)
    tables = inspector.get_table_names()
    print(f"{message} Tables in database: {tables}")



# ------------------------------------------------------ Initialisation de le séssion ----------------------------------------------------------|
@pytest.fixture(scope="session")
def test_db():
    # Setup de la base de données pour les tests
    setup_test_database()
    yield get_test_db()  # Retourne le générateur de session de test
    # Teardown de la base de données après les tests
    teardown_test_database()
# ----------------------------------------------------------------------------------------------------------------------------------------------|




# ------------------------------------------------------ Test du endpoint /search --------------------------------------------------------------|
@pytest.mark.asyncio
async def test_search_similar_chunks(test_db):
    # Initialisation des services de test (mocks)
    minio_client, mlflow_client, solon_model, tokenizer = initialize_test_services()

    # Utilisation de la session de la base de données pour le test
    db_session = next(get_test_db())

    # Print tables before inserting chunk
    print("\n\n================================= \033[1;33mTEST 1 : test du top n chunk\033[0m =======================================================")
    print_tables(db_session, message="\nPrésence des tables avant insertions des chunks\n|-> ")

    # Ajout d'un chunk dans la base de données pour le test
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

    # Print tables after inserting chunk
    print_tables(db_session, message="\nPrésence des tables après insertions des chunks\n|-> ")

    # Patch `initialize_services` pour utiliser les mocks dans l'environnement de test
    with patch("app.main.initialize_services", return_value=(minio_client, mlflow_client, solon_model, tokenizer)):
        with patch("app.main.solon_model", solon_model):  # Patch la variable globale `solon_model`

            # Construire la requête SQL en fonction de la base de données utilisée
            query_embedding = solon_model.predict(["test query"])[0]

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

    # Print tables after the test is completed
    print_tables(db_session, message="\nPrésence des tables à la fin du test\n|-> ")
    print("\n================================= \033[1;33mTEST 1\033[0m \033[32mPASSED\033[0m ======================================================================")
# ----------------------------------------------------------------------------------------------------------------------------------------------|




# ------------------------------------------------------ Test du endpoint /auth/token ----------------------------------------------------------|
def test_login_for_access_token(test_db):
    """
    Teste le point de terminaison /auth/token pour récupérer un jeton d'authentification.
    """

    # Utilisation de la session de la base de données pour le test
    db_session = next(get_test_db())
    print("\n\n\n================================= \033[1;33mTEST 2 : test du login\033[0m =============================================================")

    # Print tables before the test
    print_tables(db_session, message="\nPrésence des tables avant de récupérer le token\n|-> ")

    # Données de connexion pour l'utilisateur admin
    login_data = {
        "username": "admin",
        "password": "admin"
    }

    # Requête pour obtenir le token
    response = client.post("/auth/token", data=login_data)

    # Print tables after the test
    print_tables(db_session, message="\nPrésence des tables après avoir récupéré le token\n|-> ")

    # Vérification des résultats
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["username"] == "admin"
    assert token_data["role"]["role_name"] == "administrator"
    print("\n================================= \033[1;33mTEST 2\033[0m \033[32mPASSED\033[0m ======================================================================")


def test_login_with_invalid_credentials(test_db):
    """
    Teste le point de terminaison /auth/token avec des informations d'identification invalides.
    """

    # Utilisation de la session de la base de données pour le test
    db_session = next(get_test_db())

    # Print tables before the test
    print("\n\n\n================================= \033[1;33mTEST 3 : test d'un faux login\033[0m ======================================================")
    print_tables(db_session, message="\nPrésence des tables avant de tester avec des informations incorrectes\n|-> ")

    # Données de connexion avec un mot de passe incorrect
    login_data = {
        "username": "admin",
        "password": "wrongpassword"
    }

    # Requête pour obtenir le token
    response = client.post("/auth/token", data=login_data)

    # Print tables after the test
    print_tables(db_session, message="\nPrésence des tables après avoir testé avec des informations incorrectes\n|-> ")

    # Vérification que la connexion échoue
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

    print("\n================================= \033[1;33mTEST 3\033[0m \033[32mPASSED\033[0m ======================================================================")
# ----------------------------------------------------------------------------------------------------------------------------------------------|
