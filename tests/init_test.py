# init_test.py
import os
from unittest.mock import MagicMock
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.auth import get_password_hash

# Initialiser une base de données SQLite en mémoire pour les tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ------------------------------------------------------ Setup de la bdd de test avec sqlLite --------------------------------------------------|
def setup_test_database():
    """
    Configure la base de données en mémoire pour les tests en créant les tables et insérant des données par défaut.
    """
    # Forcer la création des tables avec SQLAlchemy
    print("\n\n==> \033[1;34mStep 1\033[0m : \033[1;32mCréation de la bdd de test...\033[0m")
    Base.metadata.create_all(bind=engine)
    print("\n\033[1;32mCréation réussie...\033[0m")

    with engine.begin() as connection:
        # Insérer les rôles par défaut
        print("\n==> \033[1;34mStep 2\033[0m : \033[1;32mInsertion des rôles et de l'utilisateur administrateur pour les tests...\033[0m")
        
        connection.execute(text("""
            INSERT INTO roles (role_name, description, author_get_doc, author_post_doc, author_put_doc, author_patch_doc, author_delete_doc, author_get_collection, author_post_collection, author_put_collection, author_patch_collection, author_delete_collection, author_get_user, author_post_user, author_put_user, author_patch_user, author_delete_user) VALUES
            ('administrator', 'Administrateur, gére les utilisateurs', true, true, true, true, true, true, true, true, true, true, true, true, true, true, true),
            ('projectManager', 'Chef de projet, gére les collections', true, true, true, true, true, true, true, true, true, true, true, false, false, false, false),
            ('user', 'Utilisateur standard, ne gére que les documents', true, true, true, true, true, true, false, false, false, false, true, false, false, false, false)
        """))

        # Hacher le mot de passe pour l'utilisateur admin
        hashed_password = get_password_hash("admin")

        # Insérer l'utilisateur administrateur
        connection.execute(text("""
            INSERT INTO users (user_id, username, passwords, email, role_id, date_de_creation, created_at) VALUES
            (1, 'admin', :hashed_password, 'admin@example.com', 1, CURRENT_DATE, CURRENT_TIMESTAMP)
        """), {"hashed_password": hashed_password})

        # Vérifications des insertions
        print("\n|-> \033[1;33mVérification des insertions...\033[0m")
        
        # Vérifier le rôle
        result = connection.execute(text("SELECT role_name FROM roles WHERE role_name = 'administrator'"))
        admin_role = result.fetchone()
        assert admin_role is not None, "\033[1;31mLe rôle 'administrator' n'a pas été inséré correctement.\033[0m"
        print("\033[1;32mLe rôle 'administrator' a bien été inséré.\033[0m")

        # Vérifier l'utilisateur
        result = connection.execute(text("SELECT username FROM users WHERE username = 'admin'"))
        admin_user = result.fetchone()
        assert admin_user is not None, "\033[1;31mL'utilisateur 'admin' n'a pas été inséré correctement.\033[0m"
        print("\033[1;32mL'utilisateur 'admin' a bien été inséré.\033[0m")

        # Vérifications de la structure
        print("\n==> \033[1;34mStep 3\033[0m : \033[1;32mChecking de la présence des tables...\033[0m")
        verify_tables_created()
        verify_columns_in_table()
# ----------------------------------------------------------------------------------------------------------------------------------------------|



# ------------------------------------------------------ Initialisation de l'env de test -------------------------------------------------------|
def initialize_test_services():
    """
    Initialise les services avec des mocks pour les tests.
    """
    print("\n==> \033[1;34mStep 4\033[0m : \033[1;32mInitialisation des services de test...\033[0m\n")

    os.environ["TESTING"] = "True"

    # Mock MinIO client
    mock_minio_client = MagicMock()
    print("\033[1;32mMock MinIO client initialisé.\033[0m")

    # Mock MLflow client
    mock_mlflow_client = MagicMock()
    print("\033[1;32mMock MLflow client initialisé.\033[0m")

    # Mock modèle Solon
    mock_solon_model = MagicMock()
    mock_solon_model.predict.return_value = [list(range(1024))]  # Retourne un vecteur constant pour les tests
    print("\033[1;32mMock modèle Solon initialisé.\033[0m")

    # Mock tokenizer
    mock_tokenizer = MagicMock()
    print("\033[1;32mMock tokenizer initialisé.\033[0m")
    print("\n==> \033[1;32mFin d'initialisation des services de test...\033[0m")

    return mock_minio_client, mock_mlflow_client, mock_solon_model, mock_tokenizer
# ----------------------------------------------------------------------------------------------------------------------------------------------|


# ------------------------------------------------------ Nettoyage de la bdd post test ---------------------------------------------------------|
def teardown_test_database():
    """
    Nettoie la base de données après les tests.
    """
    Base.metadata.drop_all(bind=engine)
# ----------------------------------------------------------------------------------------------------------------------------------------------|


# ------------------------------------------------------ Dépendance pour la bdd test -----------------------------------------------------------|
def get_test_db():
    """
    Dépendance de base de données pour les tests.
    """
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()
# ----------------------------------------------------------------------------------------------------------------------------------------------|


# ------------------------------------------------------ Check les tables ----------------------------------------------------------------------|
def verify_tables_created():
    """
    Vérifie si toutes les tables attendues ont été créées après les migrations.
    """
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("\n|-> \033[1;33mVérification de la présence des tables\033[0m")
    print("Tables in database:", tables)
    
    # Liste des tables attendues
    expected_tables = [
        "users", 
        "roles", 
        "collections", 
        "documents", 
        "chunks"
    ]
    
    # Vérifie que toutes les tables attendues sont présentes
    for table in expected_tables:
        assert table in tables, f"\033[1;31mTable {table} is missing\033[0m"
# ----------------------------------------------------------------------------------------------------------------------------------------------|


# ------------------------------------------------------ Check les colonnes dans les tables ----------------------------------------------------|
def verify_columns_in_table():
    """
    Vérifie les colonnes de chaque table spécifique.
    """
    inspector = inspect(engine)
    
    # Dictionnaire des colonnes attendues pour chaque table
    expected_columns = {
        "users": ["user_id", "username", "passwords", "email", "role_id", "date_de_creation", "created_at"],
        "roles": ["role_id", "role_name", "description", "author_get_doc", "author_post_doc", "author_put_doc",
                  "author_patch_doc", "author_delete_doc", "author_get_collection", "author_post_collection",
                  "author_put_collection", "author_patch_collection", "author_delete_collection", "author_get_user",
                  "author_post_user", "author_put_user", "author_patch_user", "author_delete_user"],
        "collections": ["collection_id", "user_id", "name", "description", "date_de_creation",
                        "derniere_modification", "etat_bucket"],
        "documents": ["document_id", "collection_id", "title", "title_document", "minio_link", "date_de_creation",
                      "created_at", "posted_by", "num_of_chunks"],
        "chunks": ["chunk_id", "document_id", "chunk_text", "taille_chunk", "embedding_cohere", 
                   "embedding_solon", "embedding_bge", "created_at"]
    }
    
    print("\n|-> \033[1;33mVérification de la présence des colonnes dans les tables\033[0m")
    # Vérifie que chaque table contient les colonnes attendues
    for table, columns in expected_columns.items():
        actual_columns = [col['name'] for col in inspector.get_columns(table)]
        for column in columns:
            assert column in actual_columns, f"\033[1;31mColumn {column} is missing in table {table}\033[0m"
        print(f"\033[1;32mAll expected columns are present in table {table}\033[0m")
# ----------------------------------------------------------------------------------------------------------------------------------------------|
