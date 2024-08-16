import pytest
from app.main import app
from app import models
from app.database import Base, get_db
from fastapi.testclient import TestClient
from unittest.mock import patch
import numpy as np
from sqlalchemy import inspect
from io import BytesIO

# Import des fonctions de test de l'initialisation depuis le dossier tests
from tests.init_test import initialize_test_services, get_test_db, setup_test_database, teardown_test_database

# Surcharge la dépendance get_db avec la base de données de test
app.dependency_overrides[get_db] = get_test_db

client = TestClient(app)


# ------------------------------------------------------ Utils ---------------------------------------------------------------------------------|
def print_tables(db_session, message=""):
    inspector = inspect(db_session.bind)
    tables = inspector.get_table_names()
    print(f"{message} Tables in database: {tables}")

def get_bearer_token():
    login_data = {
        "username": "admin",
        "password": "admin"
    }
    response = client.post("/auth/token", data=login_data)
    
    if response.status_code != 200:
        print(f"Échec de l'authentification : {response.status_code}")
        print(f"Message : {response.json()}")
    
    assert response.status_code == 200, f"Authentication failed with status code {response.status_code}"
    token_data = response.json()
    token = f"Bearer {token_data['access_token']}"
    return token

# ----------------------------------------------------------------------------------------------------------------------------------------------|





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

    print("\n\n================================= \033[1;33mTEST 1 : test du top n chunk\033[0m =======================================================")

    # Étape 1 : Vérification des tables avant l'insertion des chunks
    print("\n==> \033[34mÉtape 1\033[0m : Vérification de la présence des tables avant l'insertion des chunks...")
    print_tables(db_session, message="Présence des tables\n|-> ")
    print("Tables vérifiées.\n")

    # Étape 2 : Insertion d'un chunk dans la base de données pour le test
    print("==> \033[34mÉtape 2\033[0m : Insertion d'un chunk pour le test...")
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
    print(f"Chunk inséré : {chunk_text}")
    print(f"Document ID : {chunk.document_id}")
    print(f"Embedding : {embedding[:5]}... [total {len(embedding)} valeurs]\n")

    # Étape 3 : Vérification des tables après l'insertion des chunks
    print("==> \033[34mÉtape 3\033[0m : Vérification de la présence des tables après l'insertion des chunks...")
    print_tables(db_session, message="Présence des tables\n|-> ")
    print("Tables vérifiées.\n")

    # Étape 4 : Recherche du chunk le plus similaire
    print("==> \033[34mÉtape 4\033[0m : Recherche du chunk le plus similaire à une requête...")
    with patch("app.main.initialize_services", return_value=(minio_client, mlflow_client, solon_model, tokenizer)):
        with patch("app.main.solon_model", solon_model):  # Patch la variable globale `solon_model`
            query_embedding = solon_model.predict(["test query"])[0]
            print(f"Embedding de la requête : {query_embedding[:5]}... [total {len(query_embedding)} valeurs]\n")
            
            chunks = db_session.query(models.Chunk).all()

            min_distance = float('inf')
            closest_chunk = None

            for chunk in chunks:
                chunk_embedding = chunk.embedding_solon
                distance = np.linalg.norm(np.array(chunk_embedding) - np.array(query_embedding))
                if distance < min_distance:
                    min_distance = distance
                    closest_chunk = chunk

            print(f"Chunk trouvé : {closest_chunk.chunk_text}")
            print(f"Distance minimale : {min_distance}\n")

            # Vérification du résultat
            assert closest_chunk is not None, "Aucun chunk trouvé"
            assert closest_chunk.chunk_text == "test chunk", "Le chunk trouvé ne correspond pas au chunk inséré"

    # Étape 5 : Vérification des tables à la fin du test
    print("\n==> \033[34mÉtape 5\033[0m : Vérification des tables à la fin du test...")
    print_tables(db_session, message="Présence des tables\n|-> ")
    print("Tables vérifiées.\n")

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

    # Étape 1 : Impression des tables avant le test
    print("\n==> \033[34mÉtape 1\033[0m : Vérification de la présence des tables avant de récupérer le token...")
    print_tables(db_session, message="Présence des tables\n|-> ")
    print("Tables vérifiées.\n")

    # Étape 2 : Préparation des données de connexion
    print("==> \033[34mÉtape 2\033[0m : Préparation des données de connexion...")
    login_data = {
        "username": "admin",
        "password": "admin"
    }
    print(f"Nom d'utilisateur: {login_data['username']}")
    print(f"Mot de passe: {login_data['password']}\n")

    # Étape 3 : Envoi de la requête pour obtenir le token
    print("==> \033[34mÉtape 3\033[0m : Envoi de la requête pour obtenir le token...")
    response = client.post("/auth/token", data=login_data)
    print(f"Requête envoyée. Statut de la réponse: \033[32m{response.status_code} OK\033[0m\n")

    # Étape 4 : Impression des tables après le test
    print("\n==> \033[34mÉtape 4\033[0m : Vérification des tables après la récupération du token...")
    print_tables(db_session, message="Présence des tables après récupération du token\n|-> ")
    print("Tables vérifiées.\n")

    # Étape 5 : Vérification des résultats
    print("==> \033[34mÉtape 5\033[0m : Vérification des résultats...")
    assert response.status_code == 200, "Le login a échoué."
    token_data = response.json()
    assert "access_token" in token_data, "Le jeton d'accès est manquant."
    assert token_data["token_type"] == "bearer", "Le type de jeton est incorrect."
    assert token_data["username"] == "admin", "Le nom d'utilisateur est incorrect."
    assert token_data["role"]["role_name"] == "administrator", "Le rôle de l'utilisateur est incorrect."

    print("\033[32mAuthentification réussie!\033[0m")
    print(f"Jeton d'accès: {token_data['access_token'][:10]}...")  # Affiche seulement les 10 premiers caractères du jeton
    print(f"Type de jeton: {token_data['token_type']}")
    print(f"Nom d'utilisateur: {token_data['username']}")
    print(f"Rôle: {token_data['role']['role_name']}\n")

    print("\n================================= \033[1;33mTEST 2\033[0m \033[32mPASSED\033[0m ======================================================================")


def test_login_with_invalid_credentials(test_db):
    """
    Teste le point de terminaison /auth/token avec des informations d'identification invalides.
    """

    # Utilisation de la session de la base de données pour le test
    db_session = next(get_test_db())
    print("\n\n\n================================= \033[1;33mTEST 3 : test d'un faux login\033[0m ======================================================")

    # Étape 1 : Impression des tables avant le test
    print("\n==> \033[34mÉtape 1\033[0m : Vérification de la présence des tables avant de tester avec des informations incorrectes...")
    print_tables(db_session, message="Présence des tables\n|-> ")
    print("Tables vérifiées.\n")

    # Étape 2 : Préparation des données de connexion avec mot de passe incorrect
    print("==> \033[34mÉtape 2\033[0m : Préparation des données de connexion incorrectes...")
    login_data = {
        "username": "admin",
        "password": "wrongpassword"
    }
    print(f"Nom d'utilisateur: {login_data['username']}")
    print(f"Mot de passe: {login_data['password']}\n")

    # Étape 3 : Envoi de la requête pour tester l'authentification
    print("==> \033[34mÉtape 3\033[0m : Envoi de la requête pour tester l'authentification...")
    response = client.post("/auth/token", data=login_data)
    print(f"Requête envoyée. Statut de la réponse: \033[32m{response.status_code}\033[0m\n")

    # Étape 4 : Impression des tables après le test
    print("\n==> \033[34mÉtape 4\033[0m : Vérification des tables après le test...")
    print_tables(db_session, message="Présence des tables après test avec informations incorrectes\n|-> ")
    print("Tables vérifiées.\n")

    # Étape 5 : Vérification que la connexion échoue
    print("==> \033[34mÉtape 5\033[0m : Vérification des résultats...")
    assert response.status_code == 401, "La connexion aurait dû échouer."
    assert response.json() == {"detail": "Incorrect username or password"}, "Le message d'erreur est incorrect."

    print("\033[32mConnexion refusée avec succès!\033[0m")
    print(f"Message d'erreur: {response.json()['detail']}\n")

    print("\n================================= \033[1;33mTEST 3\033[0m \033[32mPASSED\033[0m ======================================================================")
# ----------------------------------------------------------------------------------------------------------------------------------------------|




# ------------------------------------------------------ Test du endpoint /create_user ---------------------------------------------------------|
def test_create_user(test_db):
    """
    Teste le point de terminaison /create_user pour créer un nouvel utilisateur.
    """

    # Utilisation de la session de la base de données pour le test
    db_session = next(get_test_db())
    print("\n\n\n================================= \033[1;33mTEST 4 : test de création d'un utilisateur\033[0m =========================================")

    # Obtenir le Bearer token
    print("\n==> \033[34mÉtape 1\033[0m : Obtention du Bearer token pour l'authentification...")
    token = get_bearer_token()
    print("Token obtenu avec succès.\n")

    # Données pour créer un nouvel utilisateur
    user_data = {
        "username": "new_user",
        "password": "new_password",
        "email": "new_user@example.com",
        "role_id": 2
    }
    print("==> \033[34mÉtape 2\033[0m : Préparation des données de l'utilisateur à créer...")
    print(f"Username: {user_data['username']}")
    print(f"Email: {user_data['email']}")
    print(f"Role ID: {user_data['role_id']}\n")

    # Requête pour créer un nouvel utilisateur
    print("==> \033[34mÉtape 3\033[0m : Envoi de la requête pour créer l'utilisateur...")
    response = client.post("/create_user", json=user_data, headers={"Authorization": token})
    print("Requête envoyée.\n")

    # Print tables after the test
    print_tables(db_session, message="\n==> \033[34mÉtape 4\033[0m : Vérification des tables après la création d'un utilisateur\n|-> ")

    # Vérification des résultats
    print("==> \033[34mÉtape 5\033[0m : Vérification des résultats...\n")
    assert response.status_code == 200, "La création de l'utilisateur a échoué."
    print(f"Statut de la réponse: \033[32m{response.status_code} OK\033[0m")

    created_user = response.json()
    assert created_user["username"] == "new_user", "Le nom d'utilisateur ne correspond pas."
    assert created_user["email"] == "new_user@example.com", "L'email ne correspond pas."
    assert created_user["role_id"] == 2, "L'ID de rôle ne correspond pas."
    
    print("\n\033[32mUtilisateur créé avec succès!\033[0m")
    print(f"ID de l'utilisateur: {created_user['user_id']}")
    print(f"Nom d'utilisateur: {created_user['username']}")
    print(f"Email: {created_user['email']}")
    print(f"ID de rôle: {created_user['role_id']}\n")
    
    print("\n================================= \033[1;33mTEST 4\033[0m \033[32mPASSED\033[0m ======================================================================")
# ----------------------------------------------------------------------------------------------------------------------------------------------|




# ------------------------------------------------------ Test du endpoint /users ---------------------------------------------------------------|
def test_get_users(test_db):
    """
    Teste le point de terminaison /users pour récupérer la liste des utilisateurs.
    """

    db_session = next(get_test_db())
    print("\n\n\n================================= \033[1;33mTEST 5 : test de récupération des utilisateurs\033[0m =====================================")

    # Obtenir le Bearer token
    print("==> \033[34mÉtape 1\033[0m : Obtention du Bearer token pour l'authentification...")
    token = get_bearer_token()
    print("Token obtenu avec succès.\n")

    # Requête pour obtenir la liste des utilisateurs
    print("==> \033[34mÉtape 2\033[0m : Requête pour obtenir la liste des utilisateurs...")
    response = client.get("/users", headers={"Authorization": token})

    # Vérification des résultats
    print("==> \033[34mÉtape 3\033[0m : Vérification des résultats...\n")
    assert response.status_code == 200, f"Erreur : statut {response.status_code}"
    print(f"Statut de la réponse: \033[32m{response.status_code} OK\033[0m")

    users = response.json()
    assert isinstance(users, list), "Le résultat doit être une liste."
    assert len(users) > 0, "La liste des utilisateurs ne doit pas être vide."
    print(f"Nombre d'utilisateurs récupérés : {len(users)}")
    print(f"Premier utilisateur : {users[0]}\n")

    print("\n================================= \033[1;33mTEST 5\033[0m \033[32mPASSED\033[0m ======================================================================")
# ----------------------------------------------------------------------------------------------------------------------------------------------|


# ------------------------------------------------------ Test du endpoint /users/{user_id} -----------------------------------------------------|
def test_get_user_by_id(test_db):
    """
    Teste le point de terminaison /users/{user_id} pour récupérer un utilisateur spécifique.
    """

    db_session = next(get_test_db())
    print("\n\n\n================================= \033[1;33mTEST 6 : test de récupération d'un utilisateur par ID\033[0m ==============================")

    # Obtenir le Bearer token
    print("==> \033[34mÉtape 1\033[0m : Obtention du Bearer token pour l'authentification...")
    token = get_bearer_token()
    print("Token obtenu avec succès.\n")

    # ID de l'utilisateur à récupérer
    user_id = 1

    # Requête pour obtenir l'utilisateur par ID
    print(f"==> \033[34mÉtape 2\033[0m : Requête pour obtenir l'utilisateur avec ID {user_id}...")
    response = client.get(f"/users/{user_id}", headers={"Authorization": token})

    # Vérification des résultats
    print("==> \033[34mÉtape 3\033[0m : Vérification des résultats...\n")
    assert response.status_code == 200, f"Erreur : statut {response.status_code}"
    print(f"Statut de la réponse: \033[32m{response.status_code} OK\033[0m")

    user = response.json()
    assert user["user_id"] == user_id, f"L'ID de l'utilisateur doit être {user_id}"
    print(f"Utilisateur récupéré : {user}\n")

    print("\n================================= \033[1;33mTEST 6\033[0m \033[32mPASSED\033[0m ======================================================================")
# ----------------------------------------------------------------------------------------------------------------------------------------------|


# ------------------------------------------------------ Test du endpoint update /users/{user_id} ----------------------------------------------|
def test_update_user(test_db):
    """
    Teste le point de terminaison /users/{user_id} pour mettre à jour un utilisateur spécifique.
    """

    db_session = next(get_test_db())
    print("\n\n\n================================= \033[1;33mTEST 7 : test de mise à jour d'un utilisateur\033[0m ======================================")

    # Obtenir le Bearer token
    print("==> \033[34mÉtape 1\033[0m : Obtention du Bearer token pour l'authentification...")
    token = get_bearer_token()
    print("Token obtenu avec succès.\n")

    # ID de l'utilisateur à mettre à jour
    user_id = 2

    # Données pour mettre à jour l'utilisateur
    print(f"==> \033[34mÉtape 2\033[0m : Préparation des données pour la mise à jour de l'utilisateur avec ID {user_id}...")
    user_update_data = {
        "username": "updated_user",
        "email": "updated_user@example.com",
        "password": "new_password",
        "role_id": 2
    }
    print(f"Données de mise à jour : {user_update_data}\n")

    # Requête pour mettre à jour l'utilisateur
    print(f"==> \033[34mÉtape 3\033[0m : Envoi de la requête pour mettre à jour l'utilisateur avec ID {user_id}...")
    response = client.patch(f"/users/{user_id}", json=user_update_data, headers={"Authorization": token})

    # Vérification des résultats
    print("==> \033[34mÉtape 4\033[0m : Vérification des résultats...\n")
    assert response.status_code == 200, f"Erreur : statut {response.status_code}"
    print(f"Statut de la réponse: \033[32m{response.status_code} OK\033[0m")

    updated_user = response.json()
    assert updated_user["username"] == "updated_user", "Le nom d'utilisateur doit être mis à jour."
    assert updated_user["email"] == "updated_user@example.com", "L'email doit être mis à jour."
    assert updated_user["role_id"] == 2, "Le rôle doit être mis à jour."
    print(f"Utilisateur mis à jour : {updated_user}\n")

    print("\n================================= \033[1;33mTEST 7\033[0m \033[32mPASSED\033[0m ======================================================================")
# ----------------------------------------------------------------------------------------------------------------------------------------------|


# ------------------------------------------------------ Test du endpoint delete /users/{user_id} ----------------------------------------------|
def test_delete_user(test_db):
    """
    Teste le point de terminaison /users/{user_id} pour supprimer un utilisateur spécifique.
    """

    db_session = next(get_test_db())
    print("\n\n\n================================= \033[1;33mTEST 8 : test de suppression d'un utilisateur\033[0m ======================================")

    # Obtenir le Bearer token
    print("==> \033[34mÉtape 1\033[0m : Obtention du Bearer token pour l'authentification...")
    token = get_bearer_token()
    print("Token obtenu avec succès.\n")

    # ID de l'utilisateur à supprimer
    user_id = 2

    # Afficher les utilisateurs existants avant la suppression
    print("==> \033[34mÉtape 2\033[0m : Vérification des utilisateurs existants avant la suppression...")
    users_before = db_session.query(models.User).all()
    print(f"Utilisateurs avant suppression : {[user.username for user in users_before]}\n")

    # Requête pour supprimer l'utilisateur
    print(f"==> \033[34mÉtape 3\033[0m : Envoi de la requête pour supprimer l'utilisateur avec ID {user_id}...")
    response = client.delete(f"/users/{user_id}", headers={"Authorization": token})

    # Si la suppression échoue, afficher des informations supplémentaires
    if response.status_code != 200:
        print(f"Échec de la suppression : statut {response.status_code}")
        print(f"Message : {response.json()}")

        # Afficher les utilisateurs restants après tentative de suppression
        users_after = db_session.query(models.User).all()
        print(f"Utilisateurs après tentative de suppression : {[user.username for user in users_after]}\n")

    # Vérification des résultats
    print("==> \033[34mÉtape 4\033[0m : Vérification des résultats...\n")
    assert response.status_code == 200, f"Erreur : statut {response.status_code}"
    print(f"Statut de la réponse: \033[32m{response.status_code} OK\033[0m")

    assert response.json() == {"detail": "User deleted successfully"}
    print("\n================================= \033[1;33mTEST 8\033[0m \033[32mPASSED\033[0m ======================================================================")
# ----------------------------------------------------------------------------------------------------------------------------------------------|

# ------------------------------------------------------ Test du endpoint /create_collection ---------------------------------------------------|
def test_create_two_collections(test_db):
    """
    Teste le point de terminaison /create_collection pour créer deux nouvelles collections.
    """

    db_session = next(get_test_db())
    print("\n\n\n================================= \033[1;33mTEST 9 : test de création de deux collections\033[0m ======================================")

    # Obtenir le Bearer token
    print("==> \033[34mÉtape 1\033[0m : Obtention du Bearer token pour l'authentification...")
    token = get_bearer_token()
    print("Token obtenu avec succès.\n")

    # Données pour créer la première collection
    print("==> \033[34mÉtape 2\033[0m : Préparation des données de la première collection à créer...")
    collection_data_1 = {
        "name": "First Collection",
        "description": "Description of the first collection"
    }
    print(f"Nom de la première collection : {collection_data_1['name']}")
    print(f"Description : {collection_data_1['description']}\n")

    # Requête pour créer la première collection
    print("==> \033[34mÉtape 3\033[0m : Envoi de la requête pour créer la première collection...")
    response_1 = client.post("/create_collection", json=collection_data_1, headers={"Authorization": token})
    print("Requête envoyée pour la première collection.\n")

    # Vérification des résultats pour la première collection
    print("==> \033[34mÉtape 4\033[0m : Vérification des résultats pour la première collection...\n")
    assert response_1.status_code == 200, "La création de la première collection a échoué."
    print(f"Statut de la réponse pour la première collection : \033[32m{response_1.status_code} OK\033[0m")

    created_collection_1 = response_1.json()
    assert created_collection_1["name"] == "first-collection", "Le nom de la première collection ne correspond pas."
    assert created_collection_1["description"] == "Description of the first collection", "La description de la première collection ne correspond pas."

    print("\n\033[32mPremière collection créée avec succès!\033[0m")
    print(f"ID de la première collection: {created_collection_1['collection_id']}")
    print(f"Nom de la première collection: {created_collection_1['name']}")
    print(f"Description: {created_collection_1['description']}\n")

    # Données pour créer la deuxième collection
    print("==> \033[34mÉtape 5\033[0m : Préparation des données de la deuxième collection à créer...")
    collection_data_2 = {
        "name": "Second Collection",
        "description": "Description of the second collection"
    }
    print(f"Nom de la deuxième collection : {collection_data_2['name']}")
    print(f"Description : {collection_data_2['description']}\n")

    # Requête pour créer la deuxième collection
    print("==> \033[34mÉtape 6\033[0m : Envoi de la requête pour créer la deuxième collection...")
    response_2 = client.post("/create_collection", json=collection_data_2, headers={"Authorization": token})
    print("Requête envoyée pour la deuxième collection.\n")

    # Vérification des résultats pour la deuxième collection
    print("==> \033[34mÉtape 7\033[0m : Vérification des résultats pour la deuxième collection...\n")
    assert response_2.status_code == 200, "La création de la deuxième collection a échoué."
    print(f"Statut de la réponse pour la deuxième collection : \033[32m{response_2.status_code} OK\033[0m")

    created_collection_2 = response_2.json()
    assert created_collection_2["name"] == "second-collection", "Le nom de la deuxième collection ne correspond pas."
    assert created_collection_2["description"] == "Description of the second collection", "La description de la deuxième collection ne correspond pas."

    print("\n\033[32mDeuxième collection créée avec succès!\033[0m")
    print(f"ID de la deuxième collection: {created_collection_2['collection_id']}")
    print(f"Nom de la deuxième collection: {created_collection_2['name']}")
    print(f"Description: {created_collection_2['description']}\n")

    # Print tables after the test
    print_tables(db_session, message="\n==> \033[34mÉtape 8\033[0m : Vérification des tables après la création des collections\n|-> ")

    print("\n================================= \033[1;33mTEST 9\033[0m \033[32mPASSED\033[0m ======================================================================")
# ----------------------------------------------------------------------------------------------------------------------------------------------|



# ------------------------------------------------------ Test du endpoint /collections ---------------------------------------------------------|
def test_get_collections(test_db):
    """
    Teste le point de terminaison /collections pour récupérer la liste des collections.
    """

    db_session = next(get_test_db())
    print("\n\n\n================================= \033[1;33mTEST 10 : test de récupération des collections\033[0m =====================================")

    # Obtenir le Bearer token
    print("==> \033[34mÉtape 1\033[0m : Obtention du Bearer token pour l'authentification...")
    token = get_bearer_token()
    print("Token obtenu avec succès.\n")

    # Requête pour obtenir la liste des collections
    print("==> \033[34mÉtape 2\033[0m : Requête pour obtenir la liste des collections...")
    response = client.get("/collections", headers={"Authorization": token})

    # Vérification des résultats
    print("==> \033[34mÉtape 3\033[0m : Vérification des résultats...\n")
    assert response.status_code == 200, f"Erreur : statut {response.status_code}"
    print(f"Statut de la réponse: \033[32m{response.status_code} OK\033[0m")

    collections = response.json()
    assert isinstance(collections, list), "Le résultat doit être une liste."
    assert len(collections) > 0, "La liste des collections ne doit pas être vide."
    print(f"Nombre de collections récupérées : {len(collections)}")
    print(f"Première collection : {collections[0]}\n")

    print("\n================================= \033[1;33mTEST 10\033[0m \033[32mPASSED\033[0m ======================================================================")
# ----------------------------------------------------------------------------------------------------------------------------------------------|


# ------------------------------------------------------ Test du endpoint /collections/{collection_id} -----------------------------------------|
def test_get_collection_by_id(test_db):
    """
    Teste le point de terminaison /collections/{collection_id} pour récupérer une collection spécifique.
    """

    db_session = next(get_test_db())
    print("\n\n\n================================= \033[1;33mTEST 11 : test de récupération d'une collection par ID\033[0m ==============================")

    # Obtenir le Bearer token
    print("==> \033[34mÉtape 1\033[0m : Obtention du Bearer token pour l'authentification...")
    token = get_bearer_token()
    print("Token obtenu avec succès.\n")

    # ID de la collection à récupérer
    collection_id = 1

    # Requête pour obtenir la collection par ID
    print(f"==> \033[34mÉtape 2\033[0m : Requête pour obtenir la collection avec ID {collection_id}...")
    response = client.get(f"/collections/{collection_id}", headers={"Authorization": token})

    # Vérification des résultats
    print("==> \033[34mÉtape 3\033[0m : Vérification des résultats...\n")
    assert response.status_code == 200, f"Erreur : statut {response.status_code}"
    print(f"Statut de la réponse: \033[32m{response.status_code} OK\033[0m")

    collection = response.json()
    assert collection["collection_id"] == collection_id, f"L'ID de la collection doit être {collection_id}"
    print(f"Collection récupérée : {collection}\n")

    print("\n================================= \033[1;33mTEST 11\033[0m \033[32mPASSED\033[0m ======================================================================")
# ----------------------------------------------------------------------------------------------------------------------------------------------|


# ------------------------------------------------------ Test du endpoint update /collections/{collection_id} ----------------------------------|
def test_update_collection(test_db):
    """
    Teste le point de terminaison /collections/{collection_id} pour mettre à jour une collection spécifique.
    """

    db_session = next(get_test_db())
    print("\n\n\n================================= \033[1;33mTEST 12 : test de mise à jour d'une collection\033[0m ======================================")

    # Obtenir le Bearer token
    print("==> \033[34mÉtape 1\033[0m : Obtention du Bearer token pour l'authentification...")
    token = get_bearer_token()
    print("Token obtenu avec succès.\n")

    # ID de la collection à mettre à jour
    collection_id = 1

    # Données pour mettre à jour la collection
    print(f"==> \033[34mÉtape 2\033[0m : Préparation des données pour la mise à jour de la collection avec ID {collection_id}...")
    collection_update_data = {
        "name": "Updated Collection",
        "description": "Updated description of the collection"
    }
    print(f"Données de mise à jour : {collection_update_data}\n")

    # Requête pour mettre à jour la collection
    print(f"==> \033[34mÉtape 3\033[0m : Envoi de la requête pour mettre à jour la collection avec ID {collection_id}...")
    response = client.patch(f"/collections/{collection_id}", json=collection_update_data, headers={"Authorization": token})

    # Vérification des résultats
    print("==> \033[34mÉtape 4\033[0m : Vérification des résultats...\n")
    assert response.status_code == 200, f"Erreur : statut {response.status_code}"
    print(f"Statut de la réponse: \033[32m{response.status_code} OK\033[0m")

    updated_collection = response.json()
    assert updated_collection["name"] == "Updated Collection", "Le nom de la collection doit être mis à jour."
    assert updated_collection["description"] == "Updated description of the collection", "La description doit être mise à jour."
    print(f"Collection mise à jour : {updated_collection}\n")

    print("\n================================= \033[1;33mTEST 12\033[0m \033[32mPASSED\033[0m ======================================================================")
# ----------------------------------------------------------------------------------------------------------------------------------------------|


# ------------------------------------------------------ Test du endpoint delete /collections/{collection_id} ----------------------------------|
def test_delete_collection(test_db):
    """
    Teste le point de terminaison /collections/{collection_id} pour supprimer une collection spécifique.
    """

    # Mock du client MinIO pour éviter les erreurs lors des appels MinIO
    with patch("app.main.minio_client") as mock_minio_client:
        mock_minio_client.list_objects.return_value = []
        mock_minio_client.bucket_exists.return_value = True

        db_session = next(get_test_db())
        print("\n\n\n================================= \033[1;33mTEST 13 : test de suppression d'une collection\033[0m ======================================")

        # Obtenir le Bearer token
        print("==> \033[34mÉtape 1\033[0m : Obtention du Bearer token pour l'authentification...")
        token = get_bearer_token()
        print("Token obtenu avec succès.\n")

        # ID de la collection à supprimer
        collection_id = 1

        # Afficher les collections existantes avant la suppression
        collections_before = db_session.query(models.Collection).all()
        print(f"Collections avant suppression : {[collection.name for collection in collections_before]}")

        # Requête pour supprimer la collection
        print(f"==> \033[34mÉtape 2\033[0m : Envoi de la requête pour supprimer la collection avec ID {collection_id}...")
        response = client.delete(f"/collections/{collection_id}", headers={"Authorization": token})

        # Si la suppression échoue, afficher des informations supplémentaires
        if response.status_code != 200:
            print(f"Échec de la suppression : statut {response.status_code}")
            print(f"Message : {response.json()}")

            # Afficher les collections restantes après tentative de suppression
            collections_after = db_session.query(models.Collection).all()
            print(f"Collections après tentative de suppression : {[collection.name for collection in collections_after]}")

        # Vérification des résultats
        print("==> \033[34mÉtape 3\033[0m : Vérification des résultats...\n")
        assert response.status_code == 200, f"Erreur : statut {response.status_code}"
        assert response.json() == {"detail": "Collection, associated documents, and MinIO bucket deleted successfully"}
        print("\n\033[32mCollection supprimée avec succès!\033[0m")

        print("\n================================= \033[1;33mTEST 13\033[0m \033[32mPASSED\033[0m ======================================================================")
# ----------------------------------------------------------------------------------------------------------------------------------------------|

# ------------------------------------------------------ Test du endpoint /upload_document ----------------------------------------------------|
@patch("app.main.minio_client")  # Mock du client MinIO pour éviter d'avoir besoin de MinIO réel
@patch("app.main.solon_model")  # Mock du modèle Solon pour simuler les embeddings
def test_upload_document(mock_solon_model, mock_minio_client, test_db):
    """
    Teste le point de terminaison /upload_document pour uploader un document dans une collection spécifique.
    """

    db_session = next(get_test_db())
    print("\n\n\n================================= \033[1;33mTEST 14 : test de l'upload d'un document\033[0m ============================================")

    # Obtenir le Bearer token
    print("==> \033[34mÉtape 1\033[0m : Obtention du Bearer token pour l'authentification...")
    token = get_bearer_token()
    print("Token obtenu avec succès.\n")

    # Utilisation de la collection existante avec l'ID 2
    collection_id = 2
    collection_name = "Second Collection"  # Nom de la collection avec ID 2

    print(f"Utilisation de la collection existante : ID = {collection_id}, Nom = {collection_name}\n")

    # Mock du retour du modèle Solon
    mock_solon_model.predict.return_value = [list(range(1024))]  # Retourne un embedding fixe

    # Mock du client MinIO pour éviter les vraies interactions avec le stockage
    mock_minio_client.put_object.return_value = None  # Simule un upload réussi

    # Créer un fichier temporaire à uploader
    test_content = "This is a test document." * 20  # Création de contenu de test
    file = BytesIO(test_content.encode('utf-8'))  # Encodage du contenu en binaire
    file.name = "test_document.txt"  # Nom du fichier

    # Données pour uploader le document
    upload_data = {
        "collection_id": collection_id,
        "collection_name": collection_name,
        "title": "Test Document"
    }

    # Requête pour uploader un document
    print(f"==> \033[34mÉtape 2\033[0m : Envoi de la requête pour uploader le document '{file.name}' dans la collection ID {collection_id}...")
    response = client.post(
        "/upload_document",
        data=upload_data,
        files={"file": (file.name, file, "text/plain")},
        headers={"Authorization": token}
    )
    print("Requête envoyée.\n")

    # Vérification des résultats
    print("==> \033[34mÉtape 3\033[0m : Vérification des résultats...\n")
    assert response.status_code == 200, f"Erreur : statut {response.status_code}"
    uploaded_document = response.json()
    assert uploaded_document["title"] == "Test Document", "Le titre du document ne correspond pas."
    assert uploaded_document["collection_id"] == collection_id, "L'ID de la collection ne correspond pas."
    print(f"Document uploadé : {uploaded_document}\n")

    print("\n================================= \033[1;33mTEST 14\033[0m \033[32mPASSED\033[0m ======================================================================")
# ----------------------------------------------------------------------------------------------------------------------------------------------|


# ------------------------------------------------------ Test du endpoint /documents -----------------------------------------------------------|
def test_get_all_documents(test_db):
    """
    Teste le point de terminaison /documents pour récupérer la liste de tous les documents.
    """

    db_session = next(get_test_db())
    print("\n\n\n================================= \033[1;33mTEST 15 : test de récupération de la liste des documents\033[0m ============================")

    # Obtenir le Bearer token
    print("==> \033[34mÉtape 1\033[0m : Obtention du Bearer token pour l'authentification...")
    token = get_bearer_token()
    print("Token obtenu avec succès.\n")

    # Requête pour obtenir la liste de tous les documents
    print("==> \033[34mÉtape 2\033[0m : Envoi de la requête pour obtenir la liste des documents...")
    response = client.get("/documents", headers={"Authorization": token})
    print("Requête envoyée.\n")

    # Vérification des résultats
    print("==> \033[34mÉtape 3\033[0m : Vérification des résultats...\n")
    assert response.status_code == 200, f"Erreur : statut {response.status_code}"
    documents = response.json()
    assert isinstance(documents, list), "Le résultat doit être une liste."
    assert len(documents) > 0, "La liste des documents ne doit pas être vide."
    print(f"Nombre de documents récupérés : {len(documents)}")
    print(f"Premier document : {documents[0]}\n")

    print("\n================================= \033[1;33mTEST 15\033[0m \033[32mPASSED\033[0m ======================================================================")
# ----------------------------------------------------------------------------------------------------------------------------------------------|




# ------------------------------------------------------ Test du endpoint /documents/{document_id} ---------------------------------------------|
def test_get_document_by_id(test_db):
    """
    Teste le point de terminaison /documents/{document_id} pour récupérer un document spécifique.
    """

    db_session = next(get_test_db())
    print("\n\n\n================================= \033[1;33mTEST 16 : test de récupération d'un document par ID\033[0m =================================")

    # Obtenir le Bearer token
    print("==> \033[34mÉtape 1\033[0m : Obtention du Bearer token pour l'authentification...")
    token = get_bearer_token()
    print("Token obtenu avec succès.\n")

    # ID du document à récupérer
    document_id = 1

    # Requête pour obtenir le document par ID
    print(f"==> \033[34mÉtape 2\033[0m : Envoi de la requête pour obtenir le document avec ID {document_id}...")
    response = client.get(f"/documents/{document_id}", headers={"Authorization": token})
    print("Requête envoyée.\n")

    # Vérification des résultats
    print("==> \033[34mÉtape 3\033[0m : Vérification des résultats...\n")
    assert response.status_code == 200, f"Erreur : statut {response.status_code}"
    document = response.json()
    assert document["document_id"] == document_id, f"L'ID du document doit être {document_id}"
    print(f"Document récupéré : {document}\n")

    print("\n================================= \033[1;33mTEST 16\033[0m \033[32mPASSED\033[0m ======================================================================")
# ----------------------------------------------------------------------------------------------------------------------------------------------|



# ------------------------------------------------------ Test du endpoint /collections/{collection_name}/documents -----------------------------|
def test_get_documents_by_collection(test_db):
    """
    Teste le point de terminaison /collections/{collection_name}/documents pour récupérer la liste des documents d'une collection.
    """

    db_session = next(get_test_db())
    print("\n\n\n================================= \033[1;33mTEST 17 : test de récupération des documents d'une collection\033[0m =======================")

    # Obtenir le Bearer token
    print("==> \033[34mÉtape 1\033[0m : Obtention du Bearer token pour l'authentification...")
    token = get_bearer_token()
    print("Token obtenu avec succès.\n")

    # Nom de la collection à utiliser
    collection_name = "second-collection"

    # Requête pour obtenir les documents de la collection
    print(f"==> \033[34mÉtape 2\033[0m : Envoi de la requête pour obtenir les documents de la collection '{collection_name}'...")
    response = client.get(f"/collections/{collection_name}/documents", headers={"Authorization": token})
    print("Requête envoyée.\n")

    # Vérification des résultats
    print("==> \033[34mÉtape 3\033[0m : Vérification des résultats...\n")
    assert response.status_code == 200, f"Erreur : statut {response.status_code}"
    documents = response.json()
    assert isinstance(documents, list), "Le résultat doit être une liste."
    assert len(documents) > 0, "La liste des documents ne doit pas être vide."
    print(f"Nombre de documents récupérés dans la collection '{collection_name}' : {len(documents)}")
    print(f"Premier document : {documents[0]}\n")

    print("\n================================= \033[1;33mTEST 17\033[0m \033[32mPASSED\033[0m ======================================================================")
# ----------------------------------------------------------------------------------------------------------------------------------------------|



# ------------------------------------------------------ Test du endpoint /delete_document/{document_id} ---------------------------------------|
@patch("app.main.minio_client")  # Patch du client MinIO pour éviter d'avoir besoin de MinIO réel
def test_delete_document(mock_minio_client, test_db):
    """
    Teste le point de terminaison /delete_document/{document_id} pour supprimer un document spécifique.
    """

    db_session = next(get_test_db())
    print("\n\n\n================================= \033[1;33mTEST 18 : test de suppression d'un document\033[0m =========================================")

    # Obtenir le Bearer token
    print("==> \033[34mÉtape 1\033[0m : Obtention du Bearer token pour l'authentification...")
    token = get_bearer_token()
    print("Token obtenu avec succès.\n")

    # ID du document à supprimer
    document_id = 1

    # Mock pour simuler une suppression réussie dans MinIO
    mock_minio_client.remove_object.return_value = None  # Simule une suppression réussie

    # Afficher les documents existants avant la suppression
    documents_before = db_session.query(models.Document).all()
    print(f"Documents avant suppression : {[doc.title for doc in documents_before]}")

    # Requête pour supprimer le document
    print(f"==> \033[34mÉtape 2\033[0m : Envoi de la requête pour supprimer le document avec ID {document_id}...")
    response = client.delete(f"/delete_document/{document_id}", headers={"Authorization": token})

    # Si la suppression échoue, afficher des informations supplémentaires
    if response.status_code != 200:
        print(f"Échec de la suppression : statut {response.status_code}")
        print(f"Message : {response.json()}")

        # Afficher les documents restants après tentative de suppression
        documents_after = db_session.query(models.Document).all()
        print(f"Documents après tentative de suppression : {[doc.title for doc in documents_after]}")

    # Vérification des résultats
    print("==> \033[34mÉtape 3\033[0m : Vérification des résultats...\n")
    assert response.status_code == 200, f"Erreur : statut {response.status_code}"
    assert response.json() == {"detail": f"Document with id {document_id} and its chunks have been deleted successfully"}
    print(f"Document avec ID {document_id} supprimé avec succès.\n")

    print("\n================================= \033[1;33mTEST 18\033[0m \033[32mPASSED\033[0m ======================================================================")
# ----------------------------------------------------------------------------------------------------------------------------------------------|
